"""
MongoDB-native GraphRAG engine implementing Microsoft GraphRAG's core concepts.

Architecture:
- Entities: Projects, Companies, Contacts loaded from MongoDB
- Relationships: Adjacency graph from relationships collection
- Communities: Province-based clustering (each unique province = 1 community)
- Community Reports: Gemma4-generated summaries (cached in-memory)
- Local search: BM25-style text scoring + neighborhood expansion (2 hops)
- Global search: Relevant communities selected by query → synthesized by Gemma4

Data schema from MongoDB:
- projects: {name, province, status, category, developer, value_billion_vnd, description, entity_key, code}
- contacts: {full_name, company, role, phone, email, entity_key}
- companies: {name, entity_key}
- relationships: {source_id, target_id, role_type, source_type, target_type, unique_key}

This is a pure in-memory engine with no file-based indexing phase.
All LLM tasks use Gemma4 via core.ai_client.
"""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Optional

from unidecode import unidecode


# 5 thành phố trực thuộc trung ương (không phải tỉnh)
_CENTRAL_CITIES = {
    "hà nội", "hồ chí minh", "đà nẵng", "hải phòng", "cần thơ",
}

_LOC_PREFIX_RE = re.compile(
    r"^(?:thành phố|tỉnh|tp\.\s*|tp\s+)",
    re.IGNORECASE | re.UNICODE,
)


def _location_label(province: str) -> str:
    """Return 'Thành phố' or 'Tỉnh' based on Vietnam's administrative classification."""
    norm = _LOC_PREFIX_RE.sub("", province).strip().lower()
    return "Thành phố" if norm in _CENTRAL_CITIES else "Tỉnh/TP"


def _normalize_query_location(query: str) -> str:
    """Strip location prefixes from query so 'thành phố Hồ Chí Minh' → 'Hồ Chí Minh'."""
    return _LOC_PREFIX_RE.sub("", query.strip())


def _slugify(text: str) -> str:
    """Convert text to slug format (lowercase, hyphens, ASCII only)."""
    text = unidecode(text).lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-") or "unknown"


@dataclass
class Entity:
    """Represents a searchable entity in the graph (project, company, or contact)."""

    id: str  # Unique identifier (entity_key or _id)
    name: str  # Display name
    type: str  # "project" | "company" | "contact"
    community_id: str  # slugified province name or "unknown"
    text: str  # Concatenated searchable text
    properties: dict  # Type-specific metadata (province, status, role, etc.)


@dataclass
class Community:
    """Represents a province-based community of entities."""

    id: str  # slugified province name
    label: str  # display name (e.g., "Hồ Chí Minh")
    entities: list[str]  # list of entity ids in this community
    report: str  # Gemma4-generated summary (empty until generated)
    province: str  # original province name


@dataclass
class SearchResult:
    """Result from local or global search."""

    context: str  # formatted text context for LLM synthesis
    entities: list[Entity]  # relevant entities
    community_ids: list[str]  # relevant community ids
    method: str  # "local" | "global"


class MongoGraphRAG:
    """
    In-memory GraphRAG engine backed by MongoDB data.

    Lazy-loads all entities and relationships on first query.
    Generates community reports on-demand and caches them.
    """

    def __init__(self) -> None:
        """Initialize the GraphRAG engine (index not built until first query)."""
        self._built = False
        self._lock = asyncio.Lock()
        self._entities: dict[str, Entity] = {}  # id → Entity
        self._adj: dict[str, list[str]] = {}  # id → [related_ids]
        self._communities: dict[str, Community] = {}  # community_id → Community
        self._entity_list: list[Entity] = []  # for iteration

    async def ensure_index(self) -> None:
        """Build index once, lazily. Safe for concurrent calls."""
        if self._built:
            return
        async with self._lock:
            if not self._built:
                await self._build_index()
                self._built = True

    async def _build_index(self) -> None:
        """Load all entities and relationships from MongoDB."""
        from core.database import get_db

        db = await get_db()

        # 1. Load all entities from MongoDB
        projects = await db["projects"].find({}).limit(2000).to_list(2000)
        companies = await db["companies"].find({}).limit(500).to_list(500)
        contacts = await db["contacts"].find({}).limit(2000).to_list(2000)
        relationships = await db["relationships"].find({}).limit(20000).to_list(20000)

        # 2. Create Entity objects for projects
        # Projects have explicit province → community mapping
        for p in projects:
            eid = str(p.get("entity_key") or p.get("code") or p.get("_id") or "")
            if not eid:
                continue

            province = str(p.get("province") or "")
            community_id = _slugify(province) if province else "unknown"

            # Build searchable text
            parts = [
                p.get("name") or "",
                p.get("province") or "",
                p.get("status") or "",
                p.get("category") or "",
                str(p.get("developer") or ""),
                p.get("description") or "",
            ]
            text = " ".join(str(x) for x in parts if x).strip()

            props = {
                "province": province,
                "status": p.get("status") or "",
                "value": p.get("value_billion_vnd"),
                "developer": p.get("developer") or [],
                "category": p.get("category") or "",
                "description": p.get("description") or "",
            }

            entity = Entity(
                id=eid,
                name=str(p.get("name") or eid),
                type="project",
                community_id=community_id,
                text=text,
                properties=props,
            )
            self._entities[eid] = entity
            self._adj[eid] = []

            # Register community
            if community_id not in self._communities:
                self._communities[community_id] = Community(
                    id=community_id,
                    label=province or "Khác",
                    entities=[],
                    report="",
                    province=province,
                )
            self._communities[community_id].entities.append(eid)

        # 3. Create Entity objects for companies
        for c in companies:
            eid = str(c.get("entity_key") or c.get("_id") or "")
            if not eid:
                continue

            name = str(c.get("name") or eid)
            text = name + " " + str(c.get("description") or "")
            entity = Entity(
                id=eid,
                name=name,
                type="company",
                community_id="unknown",
                text=text.strip(),
                properties=dict(c),
            )
            self._entities[eid] = entity
            self._adj[eid] = []

        # 4. Create Entity objects for contacts
        for c in contacts:
            eid = str(c.get("entity_key") or c.get("_id") or "")
            if not eid:
                continue

            name = str(c.get("full_name") or c.get("name") or eid)
            parts = [name, c.get("company") or "", c.get("role") or ""]
            text = " ".join(str(x) for x in parts if x)
            entity = Entity(
                id=eid,
                name=name,
                type="contact",
                community_id="unknown",
                text=text.strip(),
                properties={
                    "company": c.get("company") or "",
                    "role": c.get("role") or "",
                    "phone": c.get("phone") or "",
                    "email": c.get("email") or "",
                },
            )
            self._entities[eid] = entity
            self._adj[eid] = []

        # 5. Build adjacency from relationships
        # Also propagate province from projects to connected companies/contacts
        for rel in relationships:
            src = str(rel.get("source_id") or "")
            tgt = str(rel.get("target_id") or "")
            if src in self._entities and tgt in self._entities:
                if tgt not in self._adj[src]:
                    self._adj[src].append(tgt)
                if src not in self._adj[tgt]:
                    self._adj[tgt].append(src)

                # Propagate province from project to company/contact
                src_ent = self._entities[src]
                tgt_ent = self._entities[tgt]

                if src_ent.type == "project" and tgt_ent.type in ("company", "contact"):
                    province = src_ent.properties.get("province") or ""
                    if province and tgt_ent.community_id == "unknown":
                        community_id = _slugify(province)
                        tgt_ent.community_id = community_id
                        if community_id in self._communities:
                            if (
                                tgt_ent.id
                                not in self._communities[community_id].entities
                            ):
                                self._communities[community_id].entities.append(
                                    tgt_ent.id
                                )

                if tgt_ent.type == "project" and src_ent.type in ("company", "contact"):
                    province = tgt_ent.properties.get("province") or ""
                    if province and src_ent.community_id == "unknown":
                        community_id = _slugify(province)
                        src_ent.community_id = community_id
                        if community_id in self._communities:
                            if (
                                src_ent.id
                                not in self._communities[community_id].entities
                            ):
                                self._communities[community_id].entities.append(
                                    src_ent.id
                                )

        self._entity_list = list(self._entities.values())

        print(
            f"[MongoGraphRAG] Index built: {len(self._entities)} entities, "
            f"{len(self._communities)} communities"
        )

    def _text_score(self, query: str, entity: Entity) -> float:
        """Score entity relevance to query using fuzzy matching and word overlap.

        Normalizes location prefixes so "thành phố Hồ Chí Minh" correctly
        matches entities with province = "Hồ Chí Minh".
        """
        # Normalize: strip "thành phố / tỉnh / tp." from query for cleaner matching
        q_raw   = query.lower().strip()
        q_clean = _normalize_query_location(q_raw).lower().strip()

        text = entity.text.lower()
        name = entity.name.lower()

        try:
            from rapidfuzz.fuzz import partial_ratio, token_set_ratio

            score = 0.0

            # Name match — try both raw and cleaned query
            if q_raw in name or name in q_raw or q_clean in name or name in q_clean:
                score += 15.0
            else:
                score += max(
                    token_set_ratio(q_raw, name),
                    token_set_ratio(q_clean, name),
                ) / 100.0 * 10.0

            # Text match
            score += max(
                partial_ratio(q_raw, text),
                partial_ratio(q_clean, text),
            ) / 100.0 * 3.0

            # Word overlap (both variants)
            q_words = set(q_raw.split()) | set(q_clean.split())
            text_words = set(text.split())
            score += len(q_words & text_words) * 0.5

            return score

        except ImportError:
            # Fallback without rapidfuzz
            score = 0.0
            for q in (q_raw, q_clean):
                if q in name or name in q:
                    score += 15.0
                if q in text:
                    score += 3.0
                score += len(set(q.split()) & set(text.split())) * 0.5
            return score

    def _get_neighbors(self, entity_id: str, hops: int = 2) -> list[Entity]:
        """Get neighboring entities within hop distance (BFS)."""
        visited = {entity_id}
        frontier = [entity_id]
        result = []

        for _ in range(hops):
            next_frontier = []
            for eid in frontier:
                for nid in self._adj.get(eid, []):
                    if nid not in visited:
                        visited.add(nid)
                        next_frontier.append(nid)
                        if nid in self._entities:
                            result.append(self._entities[nid])
            frontier = next_frontier
            if not frontier:
                break

        return result

    async def local_search(self, query: str, top_k: int = 8) -> SearchResult:
        """
        Local search: find top-k entities by text relevance + their neighborhoods.

        Returns SearchResult with formatted context for LLM synthesis.
        """
        await self.ensure_index()

        if not self._entity_list:
            return SearchResult(
                context="Chưa có dữ liệu trong hệ thống.",
                entities=[],
                community_ids=[],
                method="local",
            )

        # Score all entities
        scored = [(self._text_score(query, e), e) for e in self._entity_list]
        scored.sort(key=lambda x: x[0], reverse=True)

        # Take top-k with positive scores
        top_entities = [e for score, e in scored[:top_k] if score > 0.5]
        if not top_entities:
            top_entities = [e for _, e in scored[:3]]  # fallback: top 3

        # Expand neighborhoods (1 hop only for context size)
        neighbor_ids = set()
        neighbors = []
        for e in top_entities:
            for n in self._get_neighbors(e.id, hops=1):
                if n.id not in neighbor_ids:
                    neighbor_ids.add(n.id)
                    neighbors.append(n)

        # Build context string
        community_ids = list({e.community_id for e in top_entities})
        context = self._format_local_context(query, top_entities, neighbors)

        return SearchResult(
            context=context,
            entities=top_entities,
            community_ids=community_ids,
            method="local",
        )

    async def global_search(self, query: str, top_communities: int = 5) -> SearchResult:
        """
        Global search: generate/retrieve community reports and synthesize across relevant communities.

        Returns SearchResult with aggregate context for LLM synthesis.
        """
        await self.ensure_index()

        if not self._communities:
            return SearchResult(
                context="Chưa có dữ liệu cộng đồng trong hệ thống.",
                entities=[],
                community_ids=[],
                method="global",
            )

        # Pick top communities by entity count
        sorted_communities = sorted(
            self._communities.values(),
            key=lambda c: len(c.entities),
            reverse=True,
        )[:top_communities]

        # Generate missing reports (fire-and-forget style with gather)
        report_tasks = []
        for comm in sorted_communities:
            if not comm.report:
                report_tasks.append(self._generate_community_report(comm))

        if report_tasks:
            await asyncio.gather(*report_tasks, return_exceptions=True)

        # Select relevant communities by query keyword match
        q_lower = query.lower()
        ranked = []
        for comm in sorted_communities:
            score = 0.0
            if comm.province and comm.province.lower() in q_lower:
                score += 20
            if comm.report:
                try:
                    from rapidfuzz.fuzz import partial_ratio

                    score += partial_ratio(q_lower, comm.report.lower()) / 10.0
                except ImportError:
                    # Fallback: simple substring match
                    if q_lower in comm.report.lower():
                        score += 5.0
            ranked.append((score, comm))

        ranked.sort(key=lambda x: x[0], reverse=True)
        selected = [c for _, c in ranked[:top_communities]]

        # Build aggregate context
        context = self._format_global_context(query, selected)
        community_ids = [c.id for c in selected]

        return SearchResult(
            context=context,
            entities=[],
            community_ids=community_ids,
            method="global",
        )

    async def _generate_community_report(self, community: Community) -> None:
        """Use Gemma4 to generate a community summary report."""
        try:
            # Gather entity details for this community
            entities_in_comm = [
                self._entities[eid]
                for eid in community.entities[:30]  # cap at 30 for prompt size
                if eid in self._entities
            ]

            if not entities_in_comm:
                community.report = f"Cộng đồng {community.label}: Không có dữ liệu."
                return

            # Format entity list
            lines = []
            for e in entities_in_comm:
                if e.type == "project":
                    val = e.properties.get("value")
                    val_str = (
                        f" | Giá trị: {val} tỷ VND" if val else ""
                    )
                    lines.append(
                        f"- [Dự án] {e.name} | Trạng thái: "
                        f"{e.properties.get('status', 'N/A')}{val_str}"
                    )
                elif e.type == "company":
                    lines.append(f"- [Công ty/CĐT] {e.name}")
                elif e.type == "contact":
                    lines.append(
                        f"- [Liên hệ] {e.name} | {e.properties.get('role', '')} "
                        f"@ {e.properties.get('company', '')}"
                    )

            entity_text = "\n".join(lines)

            from core.ai_client import get_ai_client

            ai = get_ai_client()

            # Determine correct geographic label
            loc_lbl = _location_label(community.label)
            prompt = (
                f"""Tóm tắt ngắn gọn (3-5 câu) về thị trường bất động sản tại {loc_lbl} {community.label}.
Dựa trên danh sách thực thể sau:
{entity_text}

Tóm tắt phải bao gồm: số lượng dự án, loại hình phổ biến, chủ đầu tư nổi bật (nếu có), tổng giá trị ước tính (nếu có).
Lưu ý: {community.label} là {loc_lbl.lower()} — KHÔNG gọi là "tỉnh" nếu là thành phố trực thuộc trung ương."""
            )

            report = await ai.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300,
            )
            community.report = (
                report.strip()
                or f"Cộng đồng {community.label}: {len(entities_in_comm)} thực thể."
            )
            print(f"[GraphRAG] Generated report for community: {community.label}")

        except Exception as e:
            print(f"[GraphRAG] Report generation error for {community.label}: {e}")
            community.report = (
                f"Cộng đồng {community.label}: {len(community.entities)} thực thể."
            )

    def _format_local_context(
        self,
        query: str,
        top_entities: list[Entity],
        neighbors: list[Entity],
    ) -> str:
        """Format local search results into LLM context."""
        lines = [f"=== KẾT QUẢ TÌM KIẾM CỤC BỘ cho: '{query}' ===\n"]

        lines.append(f"--- {len(top_entities)} THỰC THỂ LIÊN QUAN ---")
        for e in top_entities:
            lines.append(self._format_entity(e))

        if neighbors:
            lines.append(f"\n--- {len(neighbors)} THỰC THỂ LIÊN KẾT ---")
            for n in neighbors[:15]:  # cap neighbors at 15
                lines.append(self._format_entity(n))

        return "\n".join(lines)

    def _format_global_context(
        self,
        query: str,
        communities: list[Community],
    ) -> str:
        """Format global search results into LLM context."""
        lines = [f"=== KẾT QUẢ TỔNG HỢP TOÀN MẠNG cho: '{query}' ===\n"]

        # Stats summary
        total_projects = sum(1 for e in self._entity_list if e.type == "project")
        total_contacts = sum(1 for e in self._entity_list if e.type == "contact")
        total_companies = sum(1 for e in self._entity_list if e.type == "company")

        lines.append(
            f"TỔNG QUAN HỆ THỐNG: {total_projects} dự án | "
            f"{total_companies} công ty/CĐT | {total_contacts} liên hệ"
        )
        lines.append(f"SỐ ĐỊA BÀN: {len(self._communities)} tỉnh/thành phố\n")

        for comm in communities:
            proj_count = sum(
                1
                for eid in comm.entities
                if eid in self._entities
                and self._entities[eid].type == "project"
            )
            lines.append(f"### Cộng đồng: {comm.label} ({proj_count} dự án)")
            if comm.report:
                lines.append(comm.report)
            lines.append("")

        return "\n".join(lines)

    def _format_entity(self, e: Entity) -> str:
        """Format a single entity for context with correct geographic labels."""
        if e.type == "project":
            props    = e.properties
            province = props.get("province") or "N/A"
            loc_lbl  = _location_label(province)   # "Thành phố" or "Tỉnh/TP"
            val      = props.get("value")
            val_str  = f" | Giá trị: {val} tỷ VND" if val else ""
            devs     = props.get("developer") or []
            dev_str  = (
                f" | CĐT: {', '.join(devs) if isinstance(devs, list) else devs}"
                if devs else ""
            )
            return (
                f"[DỰ ÁN] {e.name} | {loc_lbl}: {province} | "
                f"Trạng thái: {props.get('status', 'N/A')}{val_str}{dev_str}"
            )
        elif e.type == "company":
            return f"[CÔNG TY/CĐT] {e.name}"
        elif e.type == "contact":
            props = e.properties
            return (
                f"[LIÊN HỆ] {e.name} | Vai trò: {props.get('role', 'N/A')} | "
                f"Công ty: {props.get('company', 'N/A')} | "
                f"SĐT: {props.get('phone', 'N/A')}"
            )
        return f"[{e.type.upper()}] {e.name}"

    def get_communities_summary(self) -> list[dict]:
        """Return community data for graph visualization or reporting."""
        return [
            {
                "id": c.id,
                "label": c.label,
                "entity_count": len(c.entities),
                "report": c.report,
                "province": c.province,
            }
            for c in sorted(
                self._communities.values(),
                key=lambda x: len(x.entities),
                reverse=True,
            )
        ]

    def get_entity_community_map(self) -> dict[str, str]:
        """Return {entity_id: community_id} mapping for graph coloring."""
        return {eid: e.community_id for eid, e in self._entities.items()}

    def invalidate_index(self) -> None:
        """Reset index (call when new data is ingested to MongoDB)."""
        self._built = False
        self._entities.clear()
        self._adj.clear()
        self._communities.clear()
        self._entity_list.clear()
        print("[MongoGraphRAG] Index invalidated")


# Module-level singleton
_instance: Optional[MongoGraphRAG] = None


def get_graphrag_client() -> MongoGraphRAG:
    """Get or create the global MongoGraphRAG instance."""
    global _instance
    if _instance is None:
        _instance = MongoGraphRAG()
    return _instance
