"""
Smart RAG — Intent-aware query engine
Phan tich cau hoi → chon strategy phu hop:
  - AGGREGATE : dem, xep hang, tao bang, bao cao
  - LIST/FILTER: loc theo tinh/CĐT/trang thai
  - LOOKUP     : tim kiem tu do → dung RAG thuong
  - RELATION   : ket hop project + contact
"""
import re, json
import sqlite3
from pathlib import Path
from core.db import get_conn, row_to_dict
from core import rag as base_rag

# Intent patterns
AGGREGATE_PATTERNS = [
    r"(nhieu nhat|nhiều nhất|nhieu du an nhat|nhiều dự án nhất)",
    r"(lon nhat|lớn nhất|gia tri lon|giá trị lớn|cao nhat|cao nhất)",
    r"(bao nhieu|bao nhiêu|how many|tong so|tổng số|thong ke|thống kê)",
    r"(tong hop|tổng hợp|tạo bảng|lập bảng|tao bang|lap bang|báo cáo|bao cao)",
]

LIST_PATTERNS = [
    r"(liet ke|liệt kê|danh sach|danh sách|list|hien thi|hiển thị)",
    r"(du an o|dự án ở|du an tai|dự án tại|projects? (in|at))",
]

RELATION_PATTERNS = [
    r"(lien he|liên hệ|contact|nguoi phu trach|người phụ trách|dai dien|đại diện|ai là|ai la)",
]

def _normalize_q(query: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFD", query.lower())

def _detect_intent(query: str) -> str:
    q_norm = _normalize_q(query)
    if any(re.search(p, q_norm) for p in AGGREGATE_PATTERNS): return "aggregate"
    if any(re.search(p, q_norm) for p in RELATION_PATTERNS): return "relation"
    if any(re.search(p, q_norm) for p in LIST_PATTERNS): return "list"
    return "lookup"

def _run_aggregate(query: str) -> str:
    conn = get_conn()
    q = query.lower()
    parts = []

    # 1. Contacts by Province (The specific fix for user)
    if any(kw in q for kw in ["lien he", "contact", "nguoi"]):
        if any(kw in q for kw in ["tinh", "thanh pho", "location"]):
            rows = conn.execute("""
                SELECT p.province, COUNT(DISTINCT c.slug) as cnt
                FROM contacts c
                JOIN relationships r ON c.slug = r.target_slug
                JOIN projects p ON r.source_slug = p.slug
                WHERE p.province != ''
                GROUP BY p.province ORDER BY cnt DESC
            """).fetchall()
            if rows:
                res = "[BÁO CÁO: Số lượng liên hệ theo tỉnh thành]\n"
                res += "| Tỉnh thành | Số lượng liên hệ |\n|---|---|\n"
                for r in rows:
                    res += f"| {r[0]} | {r[1]} |\n"
                parts.append(res)

    # 2. Top Developers
    if any(kw in q for kw in ["nhieu du an", "nhiều dự án", "top", "chu dau tu"]):
        rows = conn.execute("""
            SELECT developer, COUNT(*) as cnt FROM projects 
            WHERE developer != '[]' GROUP BY developer ORDER BY cnt DESC LIMIT 5
        """).fetchall()
        if rows:
            res = "[BÁO CÁO: Top Chủ đầu tư]\n"
            for r in rows:
                try:
                    name = json.loads(r[0])[0]
                    res += f"- {name}: {r[1]} dự án\n"
                except: pass
            parts.append(res)

    conn.close()
    return "\n\n".join(parts) if parts else ""

# ... (các hàm helper khác giữ nguyên logic của Claude nhưng sửa kế thừa) ...

class SmartRAGResult(base_rag.RAGResult):
    def __init__(self):
        super().__init__()
        self.intent = "lookup"
        self.agg_text = ""

    def build_context(self) -> str:
        ctx = ""
        if self.agg_text: ctx += self.agg_text + "\n\n"
        ctx += super().build_context()
        return ctx

def search(query: str) -> SmartRAGResult:
    result = SmartRAGResult()
    intent = _detect_intent(query)
    result.intent = intent

    if intent == "aggregate":
        result.method = "aggregate_sql"
        result.agg_text = _run_aggregate(query)
    else:
        # Fallback to base RAG
        base = base_rag.search(query)
        result.projects = base.projects
        result.contacts = base.contacts
        result.method = base.method
        
    return result