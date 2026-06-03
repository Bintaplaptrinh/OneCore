"""Agent-style report generation for CoreOne.

The agent reads lightweight skill files, summarizes current supporter/project
data, asks the configured LLM for Vietnamese HTML, and saves both HTML and PDF.
It also has a deterministic fallback so Reports remains usable without an API key.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz
from unidecode import unidecode

from core.ai_client import get_ai_client
from core.database import get_stats, save_report, search_contacts, search_projects

REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports" / "agent"
SKILLS_ROOT = Path(__file__).resolve().parents[3] / "awesome_agent_skills"


def _read_skill(name: str) -> str:
    path = SKILLS_ROOT / name / "SKILL.md"
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return ""
    return text[:3200]


def _skill_bundle() -> str:
    parts = [
        _read_skill("data-analyst"),
        _read_skill("visualization-expert"),
        _read_skill("technical-writer"),
    ]
    return "\n\n---\n\n".join(part for part in parts if part.strip())


def _safe_slug(text: str) -> str:
    raw = re.sub(r"[^A-Za-z0-9_-]+", "-", unidecode(text).strip())[:64].strip("-")
    return raw or "coreone-report"


def _strip_dangerous_html(value: str) -> str:
    cleaned = re.sub(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", value or "", flags=re.I | re.S)
    cleaned = re.sub(r"\son[a-z]+\s*=\s*(['\"]).*?\1", "", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"\s(href|src)\s*=\s*(['\"])\s*javascript:.*?\2", "", cleaned, flags=re.I | re.S)
    return cleaned.strip()


def _clean_llm_json(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{.*\}", text, flags=re.S)
    if match:
        text = match.group(0)
    try:
        data = json.loads(text)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _project_snapshot(doc: dict) -> dict[str, Any]:
    developers = doc.get("developer") or []
    if isinstance(developers, str):
        developers = [developers]
    return {
        "name": str(doc.get("name") or ""),
        "province": str(doc.get("province") or ""),
        "developer": [str(item) for item in developers if str(item).strip()][:3],
        "status": str(doc.get("status") or ""),
        "value_billion_vnd": doc.get("value_billion_vnd") or 0,
        "category": str(doc.get("category") or doc.get("type") or ""),
        "notes": str(doc.get("description") or doc.get("notes") or "")[:180],
    }


def _contact_snapshot(doc: dict) -> dict[str, Any]:
    return {
        "name": str(doc.get("full_name") or doc.get("name") or ""),
        "company": str(doc.get("company") or ""),
        "role": str(doc.get("role") or ""),
        "email": str(doc.get("email") or ""),
    }


def _bar_chart(chart_id: str, title: str, rows: list[dict], label_key: str, value_key: str) -> dict:
    data = []
    for item in rows[:8]:
        label = str(item.get(label_key) or item.get("_id") or "Khác").strip() or "Khác"
        try:
            raw_value = item.get(value_key)
            if raw_value is None:
                raw_value = item.get("total_value")
            if raw_value is None:
                raw_value = item.get("count")
            if raw_value is None:
                raw_value = item.get("total")
            value = float(raw_value or 0)
        except Exception:
            value = 0
        data.append({"label": label, "value": value})
    return {"id": chart_id, "title": title, "type": "bar", "data": data}


def _chart_specs(stats: dict) -> list[dict]:
    counts = stats.get("counts") or {}
    province_rows = stats.get("projects_by_province") or []
    status_rows = stats.get("project_value_by_status") or []
    charts = [
        _bar_chart("projects_by_province", "Dự án theo khu vực", province_rows, "province", "count"),
        _bar_chart("value_by_status", "Giá trị theo trạng thái", status_rows, "status", "total_value"),
        {
            "id": "core_counts",
            "title": "Quy mô dữ liệu CoreOne",
            "type": "bar",
            "data": [
                {"label": "Dự án", "value": float(counts.get("projects") or 0)},
                {"label": "Liên hệ", "value": float(counts.get("contacts") or 0)},
                {"label": "Công ty", "value": float(counts.get("companies") or 0)},
                {"label": "Quan hệ", "value": float(counts.get("relationships") or 0)},
            ],
        },
    ]
    return [chart for chart in charts if chart.get("data")]


def _format_metric(value: Any, digits: int = 0) -> str:
    try:
        number = float(value or 0)
    except Exception:
        number = 0
    if abs(number) >= 1000:
        return f"{number:,.{digits}f}"
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.1f}"


def _format_chart_value(value: Any) -> str:
    try:
        number = float(value or 0)
    except Exception:
        number = 0
    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if abs(number) >= 1_000:
        return f"{number / 1_000:.1f}k"
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.1f}"


def _short_label(value: Any, limit: int = 34) -> str:
    text = re.sub(r"\s+", " ", str(value or "Khác")).strip() or "Khác"
    return text if len(text) <= limit else f"{text[: limit - 1].rstrip()}…"


def _normalize_charts(charts: list[dict]) -> list[dict]:
    normalized = []
    for index, chart in enumerate(charts or []):
        if not isinstance(chart, dict):
            continue
        data = []
        for item in chart.get("data") or []:
            if not isinstance(item, dict):
                continue
            try:
                value = float(item.get("value") or 0)
            except Exception:
                value = 0
            data.append({
                "label": _short_label(item.get("label")),
                "value": value,
            })
        if not data:
            continue
        chart_type = str(chart.get("type") or "bar").lower()
        if chart_type not in {"bar", "line", "pie"}:
            chart_type = "bar"
        normalized.append({
            "id": str(chart.get("id") or f"chart_{index + 1}"),
            "title": str(chart.get("title") or f"Biểu đồ {index + 1}"),
            "type": chart_type,
            "data": data[:10],
        })
    return normalized[:6]


def _svg_bar_chart(chart: dict) -> str:
    data = chart.get("data") or []
    if not data:
        return ""
    colors = ["#0058ba", "#10aebf", "#ff9f0a", "#ef536d", "#4a8eff", "#38bdf8"]
    max_value = max(float(item.get("value") or 0) for item in data) or 1
    left = 158
    top = 28
    chart_width = 386
    row_height = 28
    height = max(190, top + row_height * len(data) + 26)
    rows = []
    for index, item in enumerate(data):
        label = html.escape(_short_label(item.get("label"), 26))
        value = float(item.get("value") or 0)
        width = max(3, (value / max_value) * chart_width)
        y = top + index * row_height
        color = colors[index % len(colors)]
        rows.append(
            f'<text x="0" y="{y + 12}" font-size="10" fill="#39506f">{label}</text>'
            f'<rect x="{left}" y="{y}" width="{chart_width}" height="13" rx="6.5" fill="#e7f0fb"/>'
            f'<rect x="{left}" y="{y}" width="{width:.1f}" height="13" rx="6.5" fill="{color}"/>'
            f'<text x="{left + chart_width + 12}" y="{y + 12}" font-size="10" fill="#183656" font-weight="700">{html.escape(_format_chart_value(value))}</text>'
        )
    return (
        f'<svg class="chart-svg" viewBox="0 0 620 {height}" role="img" '
        f'aria-label="{html.escape(str(chart.get("title") or "Biểu đồ"))}">'
        '<rect x="0" y="0" width="620" height="100%" rx="14" fill="#f8fbff"/>'
        + "".join(rows)
        + "</svg>"
    )


def _chart_table(chart: dict) -> str:
    data = chart.get("data") or []
    max_value = max((float(item.get("value") or 0) for item in data), default=1) or 1
    rows = []
    for item in data[:8]:
        value = float(item.get("value") or 0)
        percent = max(2, min(100, (value / max_value) * 100))
        rows.append(
            "<tr>"
            f"<td>{html.escape(_short_label(item.get('label'), 32))}</td>"
            f'<td><span class="mini-bar"><span style="width:{percent:.1f}%"></span></span></td>'
            f"<td>{html.escape(_format_chart_value(value))}</td>"
            "</tr>"
        )
    return f'<table class="chart-data"><tbody>{"".join(rows)}</tbody></table>'


def _chart_card_html(chart: dict, compact: bool = False) -> str:
    if not chart or not chart.get("data"):
        return ""
    chart_type = "Bar" if chart.get("type") == "bar" else chart.get("type", "Chart").title()
    return f"""
    <figure class="static-chart {'is-compact' if compact else ''}">
      <figcaption>
        <span>{html.escape(str(chart.get("title") or "Biểu đồ"))}</span>
        <small>{html.escape(chart_type)} · {len(chart.get("data") or [])} nhóm</small>
      </figcaption>
      {_svg_bar_chart(chart)}
      {_chart_table(chart)}
    </figure>
    """


def _replace_chart_placeholders(body_html: str, charts: list[dict]) -> tuple[str, int]:
    chart_by_id = {str(chart.get("id")): chart for chart in charts}
    pattern = re.compile(
        r"<div\b(?=[^>]*data-chart-id=(?P<quote>['\"])(?P<id>[^'\"]+)(?P=quote))[^>]*>\s*</div>",
        flags=re.I,
    )

    def repl(match: re.Match) -> str:
        chart = chart_by_id.get(match.group("id"))
        return _chart_card_html(chart, compact=True) if chart else ""

    return pattern.subn(repl, body_html or "")


def _visual_section(charts: list[dict]) -> str:
    cards = "".join(_chart_card_html(chart) for chart in charts[:3])
    if not cards:
        return ""
    return f"""
    <section class="visual-section" data-static-charts="true">
      <div class="section-kicker">Visualization</div>
      <h2>Dashboard phân tích</h2>
      <p class="section-note">Các biểu đồ tĩnh được nhúng trực tiếp vào báo cáo để hiển thị ổn định trong HTML và PDF.</p>
      <div class="chart-grid">{cards}</div>
    </section>
    """


def _kpi_section(stats: dict) -> str:
    counts = stats.get("counts") or {}
    total_value = stats.get("project_value_total_billion_vnd") or 0
    items = [
        ("Dự án", counts.get("projects", 0), "hồ sơ đang theo dõi"),
        ("Liên hệ", counts.get("contacts", 0), "đầu mối hỗ trợ"),
        ("Công ty", counts.get("companies", 0), "pháp nhân liên quan"),
        ("Giá trị", total_value, "tỷ VND"),
    ]
    cells = "".join(
        "<td><div class=\"kpi-card\">"
        f"<span>{html.escape(label)}</span>"
        f"<strong>{html.escape(_format_metric(value, 1 if label == 'Giá trị' else 0))}</strong>"
        f"<small>{html.escape(caption)}</small>"
        "</div></td>"
        for label, value, caption in items
    )
    return f'<section class="kpi-section"><table class="kpi-table"><tr>{cells}</tr></table></section>'


def _report_cover(title: str, summary: str, query: str) -> str:
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")
    clean_query = query or "Tổng quan hệ thống CoreOne"
    return f"""
    <header class="report-cover">
      <div class="brand-row">
        <div class="brand-mark">B</div>
        <div>
          <strong>Bintaplaptrinh CoreOne</strong>
          <span>Report & Analyst</span>
        </div>
        <time>{generated_at}</time>
      </div>
      <div class="cover-content">
        <p class="eyebrow">Supporter Management Intelligence</p>
        <h1>{html.escape(title)}</h1>
        <p class="subtitle">{html.escape(summary or "Báo cáo phân tích dữ liệu hỗ trợ được tạo bằng Agent.")}</p>
      </div>
      <div class="query-box">
        <span>Yêu cầu phân tích</span>
        <p>{html.escape(clean_query)}</p>
      </div>
    </header>
    """


def _fallback_body(query: str, stats: dict, projects: list[dict], contacts: list[dict], charts: list[dict]) -> str:
    counts = stats.get("counts") or {}
    total_value = stats.get("project_value_total_billion_vnd") or 0
    top_projects = sorted(
        projects,
        key=lambda item: float(item.get("value_billion_vnd") or 0),
        reverse=True,
    )[:5]
    project_rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.get('name') or '-')}</td>"
        f"<td>{html.escape(item.get('province') or '-')}</td>"
        f"<td>{html.escape(', '.join(item.get('developer') or []) or '-')}</td>"
        f"<td>{float(item.get('value_billion_vnd') or 0):,.1f}</td>"
        "</tr>"
        for item in top_projects
    )
    contact_companies = {}
    for contact in contacts:
        company = contact.get("company") or "Chưa rõ"
        contact_companies[company] = contact_companies.get(company, 0) + 1
    company_rows = "".join(
        f"<li><strong>{html.escape(company)}</strong>: {count} liên hệ</li>"
        for company, count in sorted(contact_companies.items(), key=lambda pair: pair[1], reverse=True)[:6]
    )
    chart_refs = "".join(
        f"<div class=\"chart-placeholder\" data-chart-id=\"{html.escape(str(chart.get('id')))}\">Biểu đồ: {html.escape(str(chart.get('title') or ''))}</div>"
        for chart in charts[:3]
    )
    return f"""
    <section class="hero">
      <p class="eyebrow">Bintaplaptrinh CoreOne</p>
      <h1>Báo cáo phân tích hỗ trợ</h1>
      <p class="subtitle">Ngôn ngữ mặc định: Tiếng Việt. Truy vấn: {html.escape(query or 'Tổng quan hệ thống')}</p>
    </section>
    <section>
      <h2>1. Tóm tắt điều hành</h2>
      <p>CoreOne hiện có <strong>{counts.get('projects', 0)}</strong> dự án, <strong>{counts.get('contacts', 0)}</strong> liên hệ, <strong>{counts.get('companies', 0)}</strong> công ty và <strong>{counts.get('relationships', 0)}</strong> quan hệ dữ liệu. Tổng giá trị dự án ghi nhận khoảng <strong>{float(total_value or 0):,.1f} tỷ VND</strong>.</p>
      <p>Hệ thống nên ưu tiên chuẩn hóa thông tin liên hệ, theo dõi các nhóm dự án có giá trị lớn, và dùng biểu đồ khu vực/trạng thái để phát hiện khoảng trống dữ liệu.</p>
    </section>
    <section>
      <h2>2. Dự án nổi bật</h2>
      <table>
        <thead><tr><th>Dự án</th><th>Khu vực</th><th>Đơn vị liên quan</th><th>Giá trị tỷ VND</th></tr></thead>
        <tbody>{project_rows or '<tr><td colspan="4">Chưa có dữ liệu dự án.</td></tr>'}</tbody>
      </table>
    </section>
    <section>
      <h2>3. Mạng lưới hỗ trợ</h2>
      <ul>{company_rows or '<li>Chưa có dữ liệu liên hệ đủ để phân nhóm.</li>'}</ul>
    </section>
    <section>
      <h2>4. Biểu đồ đề xuất</h2>
      {chart_refs}
    </section>
    <section>
      <h2>5. Khuyến nghị hành động</h2>
      <ol>
        <li>Rà soát các dự án thiếu trạng thái hoặc đơn vị phụ trách.</li>
        <li>Tăng chất lượng dữ liệu liên hệ bằng cách bổ sung vai trò, email và công ty.</li>
        <li>Dùng báo cáo này trong cuộc họp vận hành để phân công cập nhật dữ liệu theo khu vực.</li>
      </ol>
    </section>
    """


def _document(
    title: str,
    body_html: str,
    summary: str,
    query: str,
    stats: dict,
    charts: list[dict],
) -> str:
    body_with_charts, replacements = _replace_chart_placeholders(body_html, charts)
    visual_html = "" if replacements else _visual_section(charts)
    embedded_attr = ' data-static-charts="true"' if charts else ""
    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <style>
    :root {{ color-scheme: light; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: Inter, Arial, sans-serif; color:#183656; background:#edf4fb; line-height:1.58; }}
    .report-document {{ max-width: 1040px; margin: 0 auto; padding: 30px; }}
    .report-cover {{ overflow:hidden; border-top:8px solid #0058ba; border-radius:18px; color:#183656; background:#fff; box-shadow:0 20px 46px rgba(0,88,186,.14); }}
    .brand-row {{ display:flex; align-items:center; gap:12px; padding:22px 26px 14px; border-bottom:1px solid #d4e3f5; }}
    .brand-mark {{ display:grid; place-items:center; width:38px; height:38px; border-radius:10px; color:#fff; background:#0058ba; font-weight:900; font-size:22px; }}
    .brand-row strong {{ display:block; font-size:14px; }}
    .brand-row span {{ display:block; color:#607696; font-size:11px; }}
    .brand-row time {{ margin-left:auto; color:#607696; font-size:12px; }}
    .cover-content {{ padding:30px 28px 22px; max-width:820px; }}
    .eyebrow, .section-kicker {{ margin:0 0 9px; color:#0058ba; font-size:11px; text-transform:uppercase; letter-spacing:.09em; font-weight:800; }}
    h1 {{ margin:0; font-size:34px; line-height:1.16; letter-spacing:0; }}
    .subtitle {{ margin:12px 0 0; max-width:760px; color:#39506f; font-size:14px; }}
    .query-box {{ margin:0 26px 26px; padding:14px 16px; border:1px solid #c9dcf2; border-radius:12px; background:#eef6ff; }}
    .query-box span {{ display:block; margin-bottom:5px; color:#0058ba; font-size:10px; text-transform:uppercase; letter-spacing:.08em; font-weight:800; }}
    .query-box p {{ margin:0; font-size:12px; }}
    section {{ margin-top:18px; padding:22px; border:1px solid #d4e3f5; border-radius:14px; background:#fff; box-shadow:0 12px 30px rgba(0,88,186,.07); }}
    .kpi-section {{ padding:0; border:0; background:transparent; box-shadow:none; }}
    .kpi-table {{ width:100%; margin:0; border-collapse:separate; border-spacing:10px 0; }}
    .kpi-table td {{ width:25%; padding:0; border:0; vertical-align:top; }}
    .kpi-card {{ min-height:116px; padding:18px; border:1px solid #d4e3f5; border-radius:14px; background:linear-gradient(180deg,#fff 0%,#f6fbff 100%); box-shadow:0 10px 24px rgba(0,88,186,.06); }}
    .kpi-card span {{ display:block; color:#607696; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.06em; }}
    .kpi-card strong {{ display:block; margin-top:9px; color:#0058ba; font-size:25px; line-height:1.05; }}
    .kpi-card small {{ display:block; margin-top:8px; color:#607696; font-size:11px; }}
    h2 {{ margin:0 0 12px; color:#0058ba; font-size:19px; line-height:1.25; }}
    h3 {{ margin:0 0 10px; color:#183656; font-size:15px; }}
    p {{ margin:8px 0; }}
    .section-note {{ color:#607696; font-size:12px; }}
    table {{ width:100%; border-collapse:collapse; margin-top:10px; font-size:12px; }}
    th, td {{ padding:9px 10px; border-bottom:1px solid #e5f0ff; text-align:left; vertical-align:top; }}
    th {{ background:#edf5ff; color:#263b5e; }}
    ul, ol {{ padding-left:22px; }}
    li {{ margin:4px 0; }}
    .chart-grid {{ display:grid; grid-template-columns:1fr; gap:14px; }}
    .static-chart {{ margin:14px 0; padding:16px; border:1px solid #d4e3f5; border-radius:14px; background:#fbfdff; break-inside:avoid; }}
    .static-chart figcaption {{ display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:10px; color:#183656; font-weight:900; }}
    .static-chart figcaption small {{ color:#607696; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; }}
    .chart-svg {{ display:block; width:100%; height:auto; margin:4px 0 10px; }}
    .chart-data {{ font-size:10.5px; margin-top:6px; }}
    .chart-data td:nth-child(1) {{ width:34%; color:#39506f; }}
    .chart-data td:nth-child(3) {{ width:64px; text-align:right; font-weight:800; color:#183656; }}
    .mini-bar {{ display:block; overflow:hidden; height:7px; border-radius:999px; background:#e7f0fb; }}
    .mini-bar span {{ display:block; height:100%; border-radius:999px; background:linear-gradient(90deg,#0058ba,#10aebf); }}
    .narrative-section > section:first-child {{ margin-top:0; }}
    .chart-placeholder {{ margin:10px 0; padding:14px 16px; border:1px dashed #6c9fff; border-radius:10px; color:#0058ba; background:#eef5ff; font-weight:700; }}
    @media (min-width: 860px) {{ .chart-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .chart-grid .static-chart:first-child {{ grid-column:1 / -1; }} }}
    @media (max-width: 760px) {{ .report-document {{ padding:18px; }} .kpi-table, .kpi-table tr, .kpi-table td {{ display:block; width:100%; }} .kpi-table {{ border-spacing:0 10px; }} h1 {{ font-size:26px; }} }}
  </style>
</head>
<body>
  <main class="report-document"{embedded_attr}>
    {_report_cover(title, summary, query)}
    {_kpi_section(stats)}
    {visual_html}
    <div class="narrative-section">{body_with_charts}</div>
  </main>
</body>
</html>"""


async def _ai_body(query: str, snapshot: dict, charts: list[dict]) -> dict[str, Any]:
    system = (
        "Bạn là Agent phân tích của Bintaplaptrinh CoreOne.\n"
        "Mặc định viết tiếng Việt. Dùng kỹ năng data-analyst, visualization-expert, technical-writer.\n"
        "Chỉ trả về JSON hợp lệ với schema: "
        "{\"title\":\"...\",\"summary\":\"...\",\"html\":\"<section>...</section>\",\"charts\":[...]}.\n"
        "HTML không được có script, iframe, style inline nguy hiểm, hay tài nguyên ngoài. "
        "Có thể đặt placeholder biểu đồ bằng <div data-chart-id=\"...\"></div>."
    )
    user = {
        "query": query,
        "skills": _skill_bundle(),
        "available_chart_specs": charts,
        "data_snapshot": snapshot,
    }
    ai = get_ai_client()
    raw = await ai.chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        temperature=0.18,
        max_tokens=3600,
    )
    return _clean_llm_json(raw)


def _extract_document_title(html_text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text or "", flags=re.I | re.S)
    if not match:
        return "CoreOne Report"
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return html.unescape(title)[:90] or "CoreOne Report"


def _stamp_pdf_pages(source_path: Path, target_path: Path, title: str) -> None:
    doc = fitz.open(str(source_path))
    total = doc.page_count
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    for index, page in enumerate(doc):
        width = page.rect.width
        page.draw_rect(fitz.Rect(0, 0, width, 66), color=None, fill=(0.0, 0.35, 0.73))
        page.draw_rect(fitz.Rect(0, 66, width, 70), color=None, fill=(0.06, 0.68, 0.75))
        page.insert_text((42, 28), "Bintaplaptrinh CoreOne", fontsize=10, fontname="helv", color=(1, 1, 1))
        page.insert_text((42, 45), "Report & Analyst", fontsize=7.5, fontname="helv", color=(0.82, 0.92, 1))
        page.insert_textbox(
            fitz.Rect(width - 220, 24, width - 42, 48),
            f"Generated {generated_at}",
            fontsize=7.5,
            fontname="helv",
            color=(0.82, 0.92, 1),
            align=fitz.TEXT_ALIGN_RIGHT,
        )
        page.draw_line((42, 778), (width - 42, 778), color=(0.78, 0.85, 0.93), width=0.6)
        page.insert_text((42, 800), "CoreOne Intelligence Report", fontsize=7.5, fontname="helv", color=(0.36, 0.46, 0.60))
        page.insert_textbox(
            fitz.Rect(width - 180, 790, width - 42, 808),
            f"{index + 1} / {total}",
            fontsize=7.5,
            fontname="helv",
            color=(0.36, 0.46, 0.60),
            align=fitz.TEXT_ALIGN_RIGHT,
        )
    doc.save(str(target_path))
    doc.close()


def _fallback_single_page_pdf(html_text: str, pdf_path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    rect = fitz.Rect(42, 88, 553, 758)
    page.insert_htmlbox(rect, html_text, scale_low=0.72)
    tmp_path = pdf_path.with_name(f"{pdf_path.stem}.fallback.pdf")
    doc.save(str(tmp_path))
    doc.close()
    _stamp_pdf_pages(tmp_path, pdf_path, _extract_document_title(html_text))
    tmp_path.unlink(missing_ok=True)


def html_to_pdf(html_text: str, pdf_path: Path) -> None:
    """Render a professional, paginated HTML report to PDF with PyMuPDF."""
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    title = _extract_document_title(html_text)
    rendered_path = pdf_path.with_name(f"{pdf_path.stem}.rendered.pdf")
    stamped_path = pdf_path.with_name(f"{pdf_path.stem}.stamped.pdf")
    for path in (rendered_path, stamped_path):
        path.unlink(missing_ok=True)

    writer = None
    try:
        story = fitz.Story(html_text)
        writer = fitz.DocumentWriter(str(rendered_path))
        page_rect = fitz.Rect(0, 0, 595, 842)
        body_rect = fitz.Rect(42, 90, 553, 760)

        def rectfn(rect_num, filled):
            return page_rect, body_rect, fitz.Matrix(1, 1)

        story.write(writer, rectfn)
        writer.close()
        writer = None
        _stamp_pdf_pages(rendered_path, stamped_path, title)
        pdf_path.unlink(missing_ok=True)
        stamped_path.replace(pdf_path)
    except Exception:
        if writer is not None:
            try:
                writer.close()
            except Exception:
                pass
        _fallback_single_page_pdf(html_text, pdf_path)
    finally:
        rendered_path.unlink(missing_ok=True)
        stamped_path.unlink(missing_ok=True)


async def generate_agent_report(query: str, language: str = "vi") -> dict[str, Any]:
    """Generate, save, and return an Agent report payload."""
    requested = (query or "").strip() or "Tạo báo cáo tổng quan hệ thống CoreOne"
    stats = await get_stats()
    raw_projects = await search_projects(query=None, filters={}, skip=0, limit=160)
    raw_contacts = await search_contacts(query=None, filters={}, skip=0, limit=160)
    projects = [_project_snapshot(item) for item in raw_projects]
    contacts = [_contact_snapshot(item) for item in raw_contacts]
    charts = _normalize_charts(_chart_specs(stats))
    snapshot = {
        "language": language or "vi",
        "stats": stats,
        "projects_sample": projects[:60],
        "contacts_sample": contacts[:60],
    }

    title = "Báo cáo phân tích CoreOne"
    summary = "Báo cáo phân tích dữ liệu hỗ trợ đã được tạo bằng Agent."
    body_html = ""

    try:
        generated = await _ai_body(requested, snapshot, charts)
        title = str(generated.get("title") or title).strip()[:120]
        summary = str(generated.get("summary") or summary).strip()[:800]
        body_html = _strip_dangerous_html(str(generated.get("html") or ""))
        if isinstance(generated.get("charts"), list) and generated["charts"]:
            generated_charts = _normalize_charts(generated["charts"])
            if generated_charts:
                charts = generated_charts
    except Exception as exc:
        print(f"[report_agent] AI fallback: {exc}")

    if not body_html:
        body_html = _fallback_body(requested, stats, projects, contacts, charts)

    full_html = _document(title, body_html, summary, requested, stats, charts)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"{ts}_{_safe_slug(title)}"
    html_path = REPORTS_DIR / f"{stem}.html"
    pdf_path = REPORTS_DIR / f"{stem}.pdf"
    html_path.write_text(full_html, encoding="utf-8")
    try:
        html_to_pdf(full_html, pdf_path)
    except Exception as exc:
        print(f"[report_agent] PDF render error: {exc}")

    report_id = await save_report(title=title, file_path=str(html_path), query=requested)
    return {
        "id": report_id,
        "title": title,
        "summary": summary,
        "html": full_html,
        "charts": charts,
        "file_path": str(html_path),
        "pdf_path": str(pdf_path),
        "download_url": f"/api/reports/{report_id}/download",
    }
