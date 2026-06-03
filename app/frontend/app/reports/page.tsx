"use client";

import { useEffect, useMemo, useState } from "react";
import { api, AgentReport, Report } from "@/lib/api";
import ReportHtmlViewer from "@/components/ReportHtmlViewer";
import {
  BarChart3,
  Download,
  Eye,
  FileText,
  Loader2,
  RefreshCw,
  Search,
  Sparkles,
} from "lucide-react";

const DEFAULT_PROMPT =
  "Tạo báo cáo phân tích tổng quan bằng tiếng Việt cho Bintaplaptrinh CoreOne, gồm insight về dự án, liên hệ, khu vực, giá trị và khuyến nghị hành động.";

function formatDate(ts: string) {
  if (!ts) return "";
  return ts.slice(0, 16).replace("T", " ");
}

function reportKindLabel(report: Report) {
  if (report.kind === "html" || report.html_available) return "HTML + PDF";
  if (report.kind === "pdf") return "PDF";
  return "Excel";
}

function toReport(report: AgentReport, query: string): Report {
  return {
    id: report.id,
    title: report.title,
    file_path: "",
    query,
    timestamp: new Date().toISOString(),
    kind: "html",
    html_available: true,
    html: report.html,
    charts: report.charts,
  };
}

function ReportCard({
  report,
  active,
  onPreview,
}: {
  report: Report;
  active: boolean;
  onPreview: () => void;
}) {
  const canPreview = !!report.html_available || !!report.html;

  return (
    <div
      className={`rounded-lg border bg-[var(--surface-container)] p-4 shadow-sm transition-all duration-200 ${
        active ? "border-accent shadow-accent/10" : "border-border hover:border-accent/35"
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-accent/10 flex-shrink-0">
          <FileText size={17} className="text-accent" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold text-text leading-snug line-clamp-2">{report.title}</p>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-[10px] text-text2">
            <span>{formatDate(report.timestamp)}</span>
            <span className="rounded bg-accent/10 px-1.5 py-0.5 text-accent">{reportKindLabel(report)}</span>
          </div>
        </div>
      </div>

      {report.query && !report.query.startsWith("summary:") && (
        <p className="mt-3 rounded-md border border-border bg-[var(--surface-container-low)] px-2.5 py-2 text-[11px] leading-relaxed text-text2 line-clamp-3">
          {report.query}
        </p>
      )}

      <div className="mt-3 flex gap-2">
        <button
          type="button"
          onClick={onPreview}
          disabled={!canPreview}
          className="btn btn-ghost flex-1 text-xs py-1.5"
          title={canPreview ? "Xem trước báo cáo HTML" : "Báo cáo này không có bản HTML"}
        >
          <Eye size={12} /> Preview
        </button>
        <a
          className="btn btn-primary flex-1 text-xs py-1.5"
          href={api.reportDownloadUrl(report.id)}
          target="_blank"
          rel="noreferrer"
        >
          <Download size={12} /> PDF
        </a>
      </div>
    </div>
  );
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState(DEFAULT_PROMPT);
  const [selected, setSelected] = useState<Report | null>(null);
  const [selectedHtml, setSelectedHtml] = useState("");

  function load() {
    setLoading(true);
    api
      .reports()
      .then((res) => {
        const next = res.data || [];
        setReports(next);
        if (!selected && next.length > 0) {
          void openReport(next[0]);
        }
      })
      .catch(() => setReports([]))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase();
    if (!needle) return reports;
    return reports.filter(
      (report) =>
        report.title.toLowerCase().includes(needle) ||
        (report.query || "").toLowerCase().includes(needle)
    );
  }, [reports, search]);

  async function openReport(report: Report) {
    setSelected(report);
    setPreviewLoading(true);
    try {
      if (report.html) {
        setSelectedHtml(report.html);
      } else if (report.html_available) {
        const res = await api.reportHtml(report.id);
        setSelectedHtml(res.html || "");
      } else {
        setSelectedHtml("");
      }
    } catch {
      setSelectedHtml("");
    } finally {
      setPreviewLoading(false);
    }
  }

  async function generateReport() {
    const prompt = query.trim() || DEFAULT_PROMPT;
    setCreating(true);
    try {
      const res = await api.createAgentReport(prompt, "vi");
      const report = res.report;
      if (!report) return;
      const nextReport = toReport(report, prompt);
      setReports((current) => [nextReport, ...current.filter((item) => item.id !== nextReport.id)]);
      setSelected(nextReport);
      setSelectedHtml(report.html);
    } finally {
      setCreating(false);
    }
  }

  const selectedCharts = selected?.charts || [];

  return (
    <div className="min-h-screen bg-bg px-8 py-8">
      <div className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-xl font-bold text-text">Report & Analyst</h1>
            <p className="text-xs text-text2">
              Agent tạo báo cáo HTML, hiển thị biểu đồ và xuất PDF. Ngôn ngữ mặc định: Tiếng Việt.
            </p>
          </div>
        </div>

        <button onClick={load} className="btn btn-ghost text-xs py-1.5 px-3 w-fit" title="Làm mới">
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      <div className="mb-6 rounded-lg border border-border bg-[var(--surface-container)] p-4 shadow-sm">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
          <label className="block">
            <span className="mb-1.5 block text-xs font-bold text-text">Yêu cầu báo cáo</span>
            <textarea
              className="input min-h-[78px] resize-none text-sm leading-relaxed"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Nhập yêu cầu phân tích..."
            />
          </label>
          <button
            type="button"
            onClick={generateReport}
            disabled={creating}
            className="btn btn-primary h-11 px-5 text-sm"
          >
            {creating ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}
            Tạo Report
          </button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
        <aside className="space-y-4">
          <div className="relative">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-text2" />
            <input
              className="input pl-8 text-sm"
              placeholder="Tìm báo cáo..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>

          {loading ? (
            <div className="flex h-44 items-center justify-center rounded-lg border border-border bg-[var(--surface-container)]">
              <Loader2 size={22} className="animate-spin text-accent" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex h-44 flex-col items-center justify-center rounded-lg border border-dashed border-border bg-[var(--surface-container-low)] text-center">
              <FileText size={28} className="text-text2/45" />
              <p className="mt-2 text-sm text-text2">Chưa có báo cáo phù hợp.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filtered.map((report) => (
                <ReportCard
                  key={report.id}
                  report={report}
                  active={selected?.id === report.id}
                  onPreview={() => openReport(report)}
                />
              ))}
            </div>
          )}
        </aside>

        <section className="min-w-0 rounded-lg border border-border bg-[var(--surface-container)] p-4 shadow-sm">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.08em] text-accent">Preview</p>
              <h2 className="mt-1 text-lg font-bold text-text">
                {selected?.title || "Chọn hoặc tạo một báo cáo"}
              </h2>
              {selected?.query && (
                <p className="mt-1 max-w-3xl text-xs leading-relaxed text-text2">{selected.query}</p>
              )}
            </div>
            {selected && (
              <a
                className="btn btn-primary text-xs py-1.5 px-3 w-fit"
                href={api.reportDownloadUrl(selected.id)}
                target="_blank"
                rel="noreferrer"
              >
                <Download size={12} /> Download PDF
              </a>
            )}
          </div>

          {previewLoading ? (
            <div className="flex h-[520px] items-center justify-center rounded-lg border border-border bg-[var(--surface-container-low)]">
              <Loader2 size={24} className="animate-spin text-accent" />
            </div>
          ) : selected ? (
            <ReportHtmlViewer html={selectedHtml || selected.html} charts={selectedCharts} />
          ) : (
            <div className="flex h-[520px] flex-col items-center justify-center rounded-lg border border-dashed border-border bg-[var(--surface-container-low)] text-center">
              <FileText size={34} className="text-text2/45" />
              <p className="mt-3 text-sm text-text2">Tạo report mới để xem phân tích HTML và biểu đồ.</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
