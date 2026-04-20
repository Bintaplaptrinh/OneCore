"""SQLite connection + all query helpers for LeadsMap backend."""
import sqlite3, json
import os
from datetime import datetime
from pathlib import Path

try:
    from pymongo import MongoClient
except Exception:  # noqa: BLE001
    MongoClient = None

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("SQLITE_DB", str(BASE_DIR / "leadsmap.db")))
REPORTS_DIR = BASE_DIR / "reports"


def _mongo_collection(name: str):
    if MongoClient is None:
        return None, None
    uri = os.getenv("MONGO_URI", "").strip()
    if not uri:
        return None, None
    db_name = os.getenv("MONGO_DB_NAME", "leadsmap").strip() or "leadsmap"
    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    return client, client[db_name][name]


# ── Bootstrap ─────────────────────────────────────────────────────────────────
def init_db():
    """Create auxiliary tables if they don't exist yet."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS query_logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            query     TEXT NOT NULL,
            answer    TEXT,
            intent    TEXT DEFAULT 'lookup',
            timestamp TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS reports (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            file_path  TEXT,
            query      TEXT,
            timestamp  TEXT DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit()
    conn.close()


# ── Connection ─────────────────────────────────────────────────────────────────
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row) -> dict:
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, str) and (v.startswith('[') or v.startswith('{')):
            try:
                d[k] = json.loads(v)
            except Exception:
                pass
    return d


# ── Projects ───────────────────────────────────────────────────────────────────
def get_projects(
    province=None, developer=None, status=None,
    type_tag=None, search=None, limit=100, offset=0,
) -> tuple[list[dict], int]:
    conn   = get_conn()
    wheres = []
    params = []

    if province:
        wheres.append("province LIKE ?")
        params.append(f"%{province}%")
    if developer:
        wheres.append("developer LIKE ?")
        params.append(f"%{developer}%")
    if status:
        wheres.append("status LIKE ?")
        params.append(f"%{status}%")
    if type_tag:
        wheres.append("type_tags LIKE ?")
        params.append(f"%{type_tag}%")
    if search:
        wheres.append("(name LIKE ? OR address LIKE ? OR notes LIKE ?)")
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]

    where_clause = ("WHERE " + " AND ".join(wheres)) if wheres else ""
    total = conn.execute(
        f"SELECT COUNT(*) FROM projects {where_clause}", params
    ).fetchone()[0]

    rows = conn.execute(
        f"SELECT * FROM projects {where_clause} LIMIT ? OFFSET ?",
        params + [limit, offset],
    ).fetchall()

    data = [row_to_dict(r) for r in rows]
    conn.close()
    return data, total


def get_project(slug: str) -> dict | None:
    conn = get_conn()
    row  = conn.execute("SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    return row_to_dict(row) if row else None


# ── Contacts ───────────────────────────────────────────────────────────────────
def get_contacts(
    company=None, search=None, limit=100, offset=0,
) -> tuple[list[dict], int]:
    conn   = get_conn()
    wheres = []
    params = []

    if company:
        wheres.append("company LIKE ?")
        params.append(f"%{company}%")
    if search:
        wheres.append("(name LIKE ? OR company LIKE ? OR role LIKE ? OR phone LIKE ? OR email LIKE ?)")
        params += [f"%{search}%"] * 5

    where_clause = ("WHERE " + " AND ".join(wheres)) if wheres else ""
    total = conn.execute(
        f"SELECT COUNT(*) FROM contacts {where_clause}", params
    ).fetchone()[0]

    rows = conn.execute(
        f"SELECT * FROM contacts {where_clause} LIMIT ? OFFSET ?",
        params + [limit, offset],
    ).fetchall()

    data = [row_to_dict(r) for r in rows]
    conn.close()
    return data, total


def get_contact(slug: str) -> dict | None:
    conn = get_conn()
    row  = conn.execute("SELECT * FROM contacts WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    return row_to_dict(row) if row else None


# ── Stats ─────────────────────────────────────────────────────────────────────
def get_stats() -> dict:
    conn = get_conn()

    total_projects     = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    total_contacts     = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
    total_relationships= conn.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]
    total_value_usd    = conn.execute(
        "SELECT COALESCE(SUM(value_usd), 0) FROM projects WHERE value_usd IS NOT NULL"
    ).fetchone()[0]
    provinces = [
        r[0] for r in
        conn.execute("SELECT DISTINCT province FROM projects WHERE province != '' ORDER BY province").fetchall()
    ]
    statuses = [
        r[0] for r in
        conn.execute("SELECT DISTINCT status FROM projects WHERE status != '' ORDER BY status").fetchall()
    ]

    conn.close()
    return {
        "total_projects":      total_projects,
        "total_contacts":      total_contacts,
        "total_relationships": total_relationships,
        "total_value_usd":     round((total_value_usd or 0) / 1_000_000, 2),
        "provinces":           provinces,
        "statuses":            statuses,
    }


# ── Graph data ────────────────────────────────────────────────────────────────
def get_graph_data() -> dict:
    conn     = get_conn()
    nodes    = []
    links    = []
    node_ids = set()

    # ── Project nodes ──────────────────────────────────────────────────────────
    projs = conn.execute(
        "SELECT slug, name, province, value_usd FROM projects"
    ).fetchall()
    for p in projs:
        nodes.append({
            "id":       p["slug"],
            "name":     p["name"] or p["slug"],
            "type":     "project",
            "color":    "#6366F1",
            "size":     6 if (p["value_usd"] or 0) > 100 else 4,
            "province": p["province"] or "",
        })
        node_ids.add(p["slug"])

    # ── Company nodes + links (from relationships) ────────────────────────────
    rels = conn.execute(
        "SELECT source_slug, target_slug, target_type, relationship FROM relationships"
    ).fetchall()
    for r in rels:
        tgt = r["target_slug"]
        if tgt not in node_ids:
            nodes.append({
                "id":    tgt,
                "name":  tgt.replace("-", " "),
                "type":  "company",
                "color": "#F59E0B",
                "size":  5,
            })
            node_ids.add(tgt)
        if r["source_slug"] in node_ids:
            links.append({
                "source": r["source_slug"],
                "target": tgt,
                "type":   r["relationship"] or "related",
            })

    # ── Contact (person) nodes — hidden until filter enabled ──────────────────
    conts = conn.execute(
        "SELECT slug, name, company, role, phone, email FROM contacts LIMIT 200"
    ).fetchall()

    # Build lookup: company name fragment → company node id
    company_lookup: dict[str, str] = {}
    for n in nodes:
        if n["type"] == "company":
            company_lookup[n["name"].lower()] = n["id"]

    for c in conts:
        nodes.append({
            "id":      c["slug"],
            "name":    c["name"] or c["slug"],
            "type":    "person",
            "color":   "#10B981",
            "size":    3,
            "hidden":  True,
            "company": c["company"] or "",
            "role":    c["role"] or "",
            "phone":   c["phone"] or "",
            "email":   c["email"] or "",
        })
        node_ids.add(c["slug"])

        # Link contact → company if there's a matching company node
        if c["company"]:
            comp_lower = c["company"].lower()
            matched_id = None
            for cname, cid in company_lookup.items():
                if comp_lower[:12] in cname or cname[:12] in comp_lower:
                    matched_id = cid
                    break

            # If no match, create a hidden company node for this contact's employer
            if not matched_id:
                hidden_co_id = f"co-{c['company'][:30].replace(' ', '')}"
                if hidden_co_id not in node_ids:
                    nodes.append({
                        "id":     hidden_co_id,
                        "name":   c["company"],
                        "type":   "company",
                        "color":  "#F59E0B",
                        "size":   4,
                        "hidden": True,
                    })
                    node_ids.add(hidden_co_id)
                    company_lookup[comp_lower] = hidden_co_id
                matched_id = hidden_co_id

            links.append({
                "source": c["slug"],
                "target": matched_id,
                "type":   "works_at",
                "hidden": True,
            })

    conn.close()
    return {"nodes": nodes, "links": links}


# ── Query log ─────────────────────────────────────────────────────────────────
def save_query_log(query: str, answer: str, intent: str = "lookup") -> None:
    client = None
    try:
        client, col = _mongo_collection("query_logs")
        if col is not None:
            col.insert_one(
                {
                    "query": query,
                    "answer": answer,
                    "intent": intent,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return
    except Exception:
        pass
    finally:
        if client is not None:
            client.close()

    conn = get_conn()
    conn.execute(
        "INSERT INTO query_logs (query, answer, intent) VALUES (?, ?, ?)",
        (query, answer, intent),
    )
    conn.commit()
    conn.close()


def get_query_history(limit: int = 30) -> list[dict]:
    client = None
    try:
        client, col = _mongo_collection("query_logs")
        if col is not None:
            rows = list(col.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
            return rows
    except Exception:
        pass
    finally:
        if client is not None:
            client.close()

    conn = get_conn()
    rows = conn.execute(
        "SELECT id, query, answer, intent, timestamp FROM query_logs ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Reports vault ─────────────────────────────────────────────────────────────
def save_report(title: str, file_path: str, query: str = "") -> int:
    conn = get_conn()
    cur  = conn.execute(
        "INSERT INTO reports (title, file_path, query) VALUES (?, ?, ?)",
        (title, file_path, query),
    )
    report_id = int(cur.lastrowid or 0)
    conn.commit()
    conn.close()
    return report_id


def get_reports() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, title, file_path, query, timestamp FROM reports ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_report(report_id: int) -> dict | None:
    conn = get_conn()
    row  = conn.execute(
        "SELECT id, title, file_path, query, timestamp FROM reports WHERE id = ?",
        (report_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None