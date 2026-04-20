"""
RAG Engine: LanceDB vector search + SQLite metadata context
- Uu tien LanceDB (semantic search) neu da build index
- Fallback SQLite LIKE search neu LanceDB chua build
"""
import json
import os
import sqlite3
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent.parent / ".env")

BASE_DIR     = Path(__file__).resolve().parents[1]
DB_PATH      = Path(os.getenv("SQLITE_DB", str(BASE_DIR / "leadsmap.db")))
LANCEDB_PATH = Path(os.getenv("LANCEDB_PATH", str(BASE_DIR / "lancedb_store")))
EMBED_MODEL  = os.getenv("FPT_EMBEDDING_MODEL", "multilingual-e5-large")
RERANK_MODEL = os.getenv("FPT_RERANKER_MODEL", "bge-reranker-v2-m3")
EMBED_DIMS   = int(os.getenv("FPT_EMBEDDING_DIMS", "1024"))
TOP_K        = 6
TOP_SQL      = 8


def _normalize_base_url(raw_url: str) -> str:
    """Normalize API URL into base URL for OpenAI-compatible clients."""
    url = raw_url.strip().rstrip("/")
    if not url:
        return "https://mkp-api.fptcloud.com"
    if url.endswith("/chat/completions"):
        return url[: -len("/chat/completions")]
    return url


def _get_fpt_client() -> OpenAI | None:
    api_key = (os.getenv("FPT_API", "") or os.getenv("FPT_API_KEY", "")).strip()
    if not api_key:
        return None

    raw_url = os.getenv("FPT_BASE_URL", "") or os.getenv("FPT_API_URL", "")
    base_url = _normalize_base_url(raw_url)
    return OpenAI(api_key=api_key, base_url=base_url)

def _row_to_dict(row) -> dict:
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, str) and v.startswith('['):
            try:
                d[k] = json.loads(v)
            except Exception:
                pass
    return d


class RAGResult:
    def __init__(self, method: str = "sqlite"):
        self.method   = method
        self.projects: list[dict] = []
        self.contacts: list[dict] = []
        self.chunks:   list[dict] = []
        self.intent    = "lookup"

    def build_context(self) -> str:
        parts = []

        for c in self.chunks[:TOP_K]:
            parts.append(f"[CHUNK tu {c['slug']}]\n{c['text']}")

        for p in self.projects:
            devs = p.get("developer", [])
            if isinstance(devs, list): devs = ", ".join(devs)
            tags = p.get("type_tags", [])
            if isinstance(tags, list): tags = ", ".join(tags)
            parts.append(
                f"[DU AN] {p['name']} | Tinh: {p.get('province','?')} | "
                f"CDT: {devs} | Gia tri: {p.get('value_str','N/A')} | "
                f"Trang thai: {p.get('status','?')} | Loai: {tags} | "
                f"Khoi cong: {p.get('groundbreaking','?')} | Ban giao: {p.get('handover','?')} | "
                f"Ghi chu: {p.get('notes','')}"
            )

        for c in self.contacts:
            parts.append(
                f"[LIEN HE] {c['name']} | Cong ty: {c.get('company','?')} | "
                f"Vai tro: {c.get('role','?')} | "
                f"SDT: {c.get('phone','?')} | Email: {c.get('email','?')}"
            )

        return "\n\n".join(parts) if parts else "Khong tim thay du lieu lien quan."

    def get_citations(self) -> List[Dict]:
        seen, cits = set(), []
        for p in self.projects:
            if p.get("slug") not in seen:
                seen.add(p["slug"])
                cits.append({"name": p["name"], "type": "project", "slug": p["slug"]})
        for c in self.contacts:
            if c.get("slug") not in seen:
                seen.add(c["slug"])
                cits.append({"name": c["name"], "type": "contact", "slug": c["slug"]})
        return cits


# ── Embedding ──────────────────────────────────────────────────────────────────
def _embed_query(query: str) -> list[float] | None:
    client = _get_fpt_client()
    if client is None:
        return None

    try:
        response = client.embeddings.create(
            model=EMBED_MODEL,
            input=[query],
            dimensions=EMBED_DIMS,
            encoding_format="float",
            input_text_truncate="none",
            input_type="query",
        )
        if response.data and response.data[0].embedding:
            return response.data[0].embedding
    except TypeError:
        # Fallback for providers that only support standard OpenAI params.
        try:
            response = client.embeddings.create(
                model=EMBED_MODEL,
                input=[query],
            )
            if response.data and response.data[0].embedding:
                return response.data[0].embedding
        except Exception as e:
            print(f"[RAG] Embed fallback error: {e}")
            return None
    except Exception as e:
        print(f"[RAG] Embed error: {e}")
        return None

    return None


def _rerank_chunks(query: str, chunks: list[dict], top_n: int) -> list[dict]:
    """Optional rerank step using FPT reranker endpoint."""
    if not chunks:
        return []

    client = _get_fpt_client()
    if client is None:
        return chunks[:top_n]

    try:
        base_url = str(client.base_url).rstrip("/")
        response = client._client.post(
            f"{base_url}/v1/rerank",
            json={
                "model": RERANK_MODEL,
                "query": query,
                "documents": [c["text"] for c in chunks],
                "top_n": top_n,
            },
            headers={
                "Authorization": f"Bearer {client.api_key}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        payload = response.json()
        ranking = payload.get("results") or payload.get("data") or []

        reranked: list[dict] = []
        for item in ranking:
            idx = item.get("index")
            if isinstance(idx, int) and 0 <= idx < len(chunks):
                row = dict(chunks[idx])
                row["rerank_score"] = float(item.get("relevance_score", 0.0))
                reranked.append(row)

        return reranked[:top_n] if reranked else chunks[:top_n]
    except Exception as e:
        print(f"[RAG] Rerank error: {e}")
        return chunks[:top_n]


# ── LanceDB vector search ──────────────────────────────────────────────────────
def _lancedb_search(query: str, top_k: int = TOP_K) -> list[dict]:
    if not LANCEDB_PATH.exists():
        return []
    try:
        import lancedb
        db = lancedb.connect(str(LANCEDB_PATH))
        if "chunks" not in db.table_names():
            return []

        vec = _embed_query(query)
        if not vec:
            return []

        tbl = db.open_table("chunks")
        # Fetch a wider candidate set before reranking.
        results = tbl.search(vec).limit(max(top_k * 3, top_k)).to_pandas()

        candidates = [
            {
                "text":     row["text"],
                "slug":     row["slug"],
                "doc_type": row.get("doc_type", "unknown"),
                "source":   row.get("source", ""),
                "score":    float(row.get("_distance", 0)),
            }
            for _, row in results.iterrows()
        ]

        return _rerank_chunks(query, candidates, top_k)
    except Exception as e:
        print(f"[RAG] LanceDB error: {e}")
        return []


# ── SQLite fallback search ─────────────────────────────────────────────────────
def _sqlite_search(query: str) -> tuple[list[dict], list[dict]]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    q    = f"%{query}%"

    proj_rows = conn.execute("""
        SELECT slug, name, province, district, developer, status, type_tags,
               value_str, groundbreaking, handover, notes, address
        FROM projects
        WHERE name LIKE ? OR notes LIKE ? OR address LIKE ?
           OR developer LIKE ? OR province LIKE ? OR type_tags LIKE ?
        LIMIT ?
    """, [q, q, q, q, q, q, TOP_SQL]).fetchall()

    cont_rows = conn.execute("""
        SELECT slug, name, company, role, phone, email
        FROM contacts
        WHERE name LIKE ? OR company LIKE ? OR role LIKE ? OR email LIKE ?
        LIMIT 5
    """, [q, q, q, q]).fetchall()

    conn.close()
    return [_row_to_dict(r) for r in proj_rows], [_row_to_dict(r) for r in cont_rows]


def _fetch_by_slugs(slugs: list[str]) -> tuple[list[dict], list[dict]]:
    if not slugs:
        return [], []
    conn   = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    params = ",".join("?" * len(slugs))

    proj_rows = conn.execute(
        f"SELECT * FROM projects WHERE slug IN ({params})", slugs
    ).fetchall()
    cont_rows = conn.execute(
        f"SELECT * FROM contacts WHERE slug IN ({params})", slugs
    ).fetchall()

    conn.close()
    return [_row_to_dict(r) for r in proj_rows], [_row_to_dict(r) for r in cont_rows]


# ── Public search function ─────────────────────────────────────────────────────
def search(query: str) -> RAGResult:
    """
    Hybrid: LanceDB semantic (if built) → SQLite LIKE fallback.
    """
    result = RAGResult()

    chunks = _lancedb_search(query)
    if chunks:
        result.chunks  = chunks
        result.method  = "lancedb"

        slugs       = list({c["slug"] for c in chunks})
        proj, cont  = _fetch_by_slugs(slugs)
        p_sql, c_sql = _sqlite_search(query)

        seen_p = {p["slug"] for p in proj}
        seen_c = {c["slug"] for c in cont}
        for p in p_sql:
            if p["slug"] not in seen_p:
                proj.append(p); seen_p.add(p["slug"])
        for c in c_sql:
            if c["slug"] not in seen_c:
                cont.append(c); seen_c.add(c["slug"])

        result.projects = proj[:8]
        result.contacts = cont[:5]
        return result

    result.projects, result.contacts = _sqlite_search(query)
    result.method = "sqlite"
    return result