"""Async MongoDB layer using motor. Production-ready implementation."""
import os
import re
from datetime import datetime
from typing import Optional
from unidecode import unidecode

import motor.motor_asyncio
from bson import ObjectId
from pymongo import ASCENDING, TEXT
from pymongo.errors import DuplicateKeyError

# MongoDB connection management
_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
_db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None


def _is_atlas_quota_error(exc: Exception) -> bool:
    """Detect Mongo Atlas free-tier quota errors (code 8000)."""
    text = str(exc).lower()
    return (
        "space quota" in text
        or "code': 8000" in text
        or '"code": 8000' in text
        or "atlaserror" in text
    )


def _log_index_error(label: str, exc: Exception) -> None:
    """Print concise index creation errors with quota-specific guidance."""
    if _is_atlas_quota_error(exc):
        print(f"[Indexes] {label} skipped: Atlas storage quota exceeded (code 8000).")
        return
    print(f"[Indexes] {label} error: {exc}")


async def init_db() -> None:
    """Initialize async MongoDB connection and create indexes."""
    global _client, _db

    mongo_uri = os.getenv("MONGO_URI", "").strip()
    db_name = os.getenv("MONGO_DB_NAME", "leadsmap").strip() or "leadsmap"

    if not mongo_uri:
        raise RuntimeError("MONGO_URI environment variable is not set")

    _client = motor.motor_asyncio.AsyncIOMotorClient(
        mongo_uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )

    # Test connection
    try:
        await _client.admin.command("ping")
        print(f"[MongoDB] Connected to {db_name}")
    except Exception as e:
        raise RuntimeError(f"Failed to connect to MongoDB: {e}")

    _db = _client[db_name]

    # Create indexes
    await _create_indexes()


async def _create_indexes() -> None:
    """Create all required indexes for collections."""
    if _db is None:
        return

    quota_blocked = False

    # Projects collection
    try:
        await _db["projects"].create_index([("entity_key", ASCENDING)], unique=True, sparse=True)
        await _db["projects"].create_index([("name", TEXT), ("province", TEXT), ("address", TEXT)])
        await _db["projects"].create_index([("created_at", ASCENDING)])
        print("[Indexes] Projects indexes created")
    except Exception as e:
        _log_index_error("Projects", e)
        if _is_atlas_quota_error(e):
            quota_blocked = True

    if quota_blocked:
        print("[Indexes] Remaining index creation skipped due to Atlas quota limit.")
        return

    # Contacts collection
    try:
        await _db["contacts"].create_index([("entity_key", ASCENDING)], unique=True, sparse=True)
        await _db["contacts"].create_index([("full_name", TEXT), ("email", TEXT), ("phone", TEXT)])
        await _db["contacts"].create_index([("created_at", ASCENDING)])
        print("[Indexes] Contacts indexes created")
    except Exception as e:
        _log_index_error("Contacts", e)
        if _is_atlas_quota_error(e):
            quota_blocked = True

    if quota_blocked:
        print("[Indexes] Remaining index creation skipped due to Atlas quota limit.")
        return

    # Companies collection
    try:
        await _db["companies"].create_index([("entity_key", ASCENDING)], unique=True, sparse=True)
        await _db["companies"].create_index([("created_at", ASCENDING)])
        print("[Indexes] Companies indexes created")
    except Exception as e:
        _log_index_error("Companies", e)
        if _is_atlas_quota_error(e):
            quota_blocked = True

    if quota_blocked:
        print("[Indexes] Remaining index creation skipped due to Atlas quota limit.")
        return

    # Relationships collection
    try:
        await _db["relationships"].create_index([("unique_key", ASCENDING)], unique=True, sparse=True)
        await _db["relationships"].create_index([("created_at", ASCENDING)])
        print("[Indexes] Relationships indexes created")
    except Exception as e:
        _log_index_error("Relationships", e)
        if _is_atlas_quota_error(e):
            quota_blocked = True

    if quota_blocked:
        print("[Indexes] Remaining index creation skipped due to Atlas quota limit.")
        return

    # Query logs collection
    try:
        await _db["query_logs"].create_index([("created_at", ASCENDING)])
        print("[Indexes] Query logs indexes created")
    except Exception as e:
        _log_index_error("Query logs", e)
        if _is_atlas_quota_error(e):
            quota_blocked = True

    if quota_blocked:
        print("[Indexes] Remaining index creation skipped due to Atlas quota limit.")
        return

    # Chat sessions collection (full conversation persistence)
    try:
        await _db["chat_sessions"].create_index([("updated_at", ASCENDING)])
        await _db["chat_sessions"].create_index([("created_at", ASCENDING)])
        print("[Indexes] Chat sessions indexes created")
    except Exception as e:
        _log_index_error("Chat sessions", e)


async def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """Get the async MongoDB database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db


def _slugify(text: str) -> str:
    """Convert text to slug format (lowercase, hyphens, ASCII only)."""
    text = unidecode(text).lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-") or "unknown"


def _try_object_id(value: str) -> ObjectId | None:
    """Convert a string to ObjectId when possible, else return None."""
    token = str(value or "").strip()
    if not token:
        return None
    try:
        return ObjectId(token)
    except Exception:
        return None


def _project_identity_filter(identifier: str) -> dict:
    """Build a resilient filter for project identity fields."""
    token = str(identifier or "").strip()
    if not token:
        return {"_id": {"$exists": False}}

    clauses = [{"entity_key": token}, {"code": token}]
    oid = _try_object_id(token)
    if oid is not None:
        clauses.append({"_id": oid})
    return {"$or": clauses}


def _contact_identity_filter(identifier: str) -> dict:
    """Build a resilient filter for contact identity fields."""
    token = str(identifier or "").strip()
    if not token:
        return {"_id": {"$exists": False}}

    clauses = [{"entity_key": token}]
    oid = _try_object_id(token)
    if oid is not None:
        clauses.append({"_id": oid})
    return {"$or": clauses}


# ─────────────────────────────────────────────────────────────────────────────
# PROJECTS
# ─────────────────────────────────────────────────────────────────────────────

async def search_projects(
    query: Optional[str] = None,
    filters: Optional[dict] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    """Search projects with full-text search and filters."""
    db = await get_db()
    filters = filters or {}

    mongo_query = {}

    # Full-text search
    if query and query.strip():
        mongo_query["$text"] = {"$search": query.strip()}

    # Apply filters
    if filters.get("province"):
        mongo_query["province"] = {"$regex": filters["province"], "$options": "i"}
    if filters.get("company"):
        mongo_query["developer"] = {"$regex": filters["company"], "$options": "i"}
    if filters.get("status"):
        mongo_query["status"] = {"$regex": filters["status"], "$options": "i"}
    if filters.get("category"):
        mongo_query["category"] = {"$regex": filters["category"], "$options": "i"}

    try:
        results = (
            await db["projects"]
            .find(mongo_query)
            .skip(skip)
            .limit(limit)
            .to_list(limit)
        )
        return results or []
    except Exception as e:
        print(f"[search_projects] Error: {e}")
        return []


async def count_projects(
    query: Optional[str] = None,
    filters: Optional[dict] = None,
) -> int:
    """Count total projects matching search and filters."""
    db = await get_db()
    filters = filters or {}

    mongo_query = {}

    if query and query.strip():
        mongo_query["$text"] = {"$search": query.strip()}

    if filters.get("province"):
        mongo_query["province"] = {"$regex": filters["province"], "$options": "i"}
    if filters.get("company"):
        mongo_query["developer"] = {"$regex": filters["company"], "$options": "i"}
    if filters.get("status"):
        mongo_query["status"] = {"$regex": filters["status"], "$options": "i"}
    if filters.get("category"):
        mongo_query["category"] = {"$regex": filters["category"], "$options": "i"}

    try:
        count = await db["projects"].count_documents(mongo_query)
        return count
    except Exception as e:
        print(f"[count_projects] Error: {e}")
        return 0


async def get_project_by_slug(slug: str) -> Optional[dict]:
    """Get a single project by slug/code."""
    db = await get_db()
    try:
        result = await db["projects"].find_one(_project_identity_filter(slug))
        return result
    except Exception as e:
        print(f"[get_project_by_slug] Error: {e}")
        return None


async def upsert_project(data: dict) -> tuple[str, bool]:
    """Upsert a project. Returns (id, created) where created=True if new."""
    db = await get_db()

    # Determine entity_key
    code = str(data.get("code") or "").strip()
    entity_key = code if code else _slugify(str(data.get("name") or ""))

    data["entity_key"] = entity_key
    data["updated_at"] = datetime.utcnow()

    if "_id" not in data:
        data["created_at"] = datetime.utcnow()

    try:
        result = await db["projects"].update_one(
            {"entity_key": entity_key},
            {"$set": data},
            upsert=True,
        )

        # Determine if it was created
        created = result.upserted_id is not None
        project_id = str(result.upserted_id or entity_key)

        return project_id, created
    except Exception as e:
        print(f"[upsert_project] Error: {e}")
        return entity_key, False


# ─────────────────────────────────────────────────────────────────────────────
# CONTACTS
# ─────────────────────────────────────────────────────────────────────────────

async def search_contacts(
    query: Optional[str] = None,
    filters: Optional[dict] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    """Search contacts with full-text search and filters."""
    db = await get_db()
    filters = filters or {}

    mongo_query = {}

    if query and query.strip():
        mongo_query["$text"] = {"$search": query.strip()}

    if filters.get("company"):
        mongo_query["company"] = {"$regex": filters["company"], "$options": "i"}

    try:
        results = (
            await db["contacts"]
            .find(mongo_query)
            .skip(skip)
            .limit(limit)
            .to_list(limit)
        )
        return results or []
    except Exception as e:
        print(f"[search_contacts] Error: {e}")
        return []


async def count_contacts(
    query: Optional[str] = None,
    filters: Optional[dict] = None,
) -> int:
    """Count total contacts matching search and filters."""
    db = await get_db()
    filters = filters or {}

    mongo_query = {}

    if query and query.strip():
        mongo_query["$text"] = {"$search": query.strip()}

    if filters.get("company"):
        mongo_query["company"] = {"$regex": filters["company"], "$options": "i"}

    try:
        count = await db["contacts"].count_documents(mongo_query)
        return count
    except Exception as e:
        print(f"[count_contacts] Error: {e}")
        return 0


async def get_contact_by_slug(slug: str) -> Optional[dict]:
    """Get a single contact by slug."""
    db = await get_db()
    try:
        result = await db["contacts"].find_one(_contact_identity_filter(slug))
        return result
    except Exception as e:
        print(f"[get_contact_by_slug] Error: {e}")
        return None


async def upsert_contact(data: dict) -> tuple[str, bool]:
    """Upsert a contact. Returns (id, created) where created=True if new."""
    db = await get_db()

    # Determine entity_key: phone > email > slugified(name + company)
    phone = str(data.get("phone") or "").strip()
    email = str(data.get("email") or "").strip()
    full_name = str(data.get("full_name") or data.get("name") or "").strip()
    company = str(data.get("company") or "").strip()

    if phone:
        entity_key = phone
    elif email:
        entity_key = email
    else:
        entity_key = _slugify(f"{full_name}-{company}" if company else full_name)

    data["entity_key"] = entity_key
    data["updated_at"] = datetime.utcnow()

    if "_id" not in data:
        data["created_at"] = datetime.utcnow()

    try:
        result = await db["contacts"].update_one(
            {"entity_key": entity_key},
            {"$set": data},
            upsert=True,
        )

        created = result.upserted_id is not None
        contact_id = str(result.upserted_id or entity_key)

        return contact_id, created
    except Exception as e:
        print(f"[upsert_contact] Error: {e}")
        return entity_key, False


# ─────────────────────────────────────────────────────────────────────────────
# COMPANIES
# ─────────────────────────────────────────────────────────────────────────────

async def upsert_company(data: dict) -> tuple[str, bool]:
    """Upsert a company. Returns (id, created) where created=True if new."""
    db = await get_db()

    name = str(data.get("name") or "").strip()
    entity_key = _slugify(name) if name else "unknown"

    data["entity_key"] = entity_key
    data["updated_at"] = datetime.utcnow()

    if "_id" not in data:
        data["created_at"] = datetime.utcnow()

    try:
        result = await db["companies"].update_one(
            {"entity_key": entity_key},
            {"$set": data},
            upsert=True,
        )

        created = result.upserted_id is not None
        company_id = str(result.upserted_id or entity_key)

        return company_id, created
    except Exception as e:
        print(f"[upsert_company] Error: {e}")
        return entity_key, False


async def get_or_create_company(name: str) -> str:
    """Get or create a company by name. Returns company id."""
    db = await get_db()
    entity_key = _slugify(name)

    try:
        existing = await db["companies"].find_one({"entity_key": entity_key})
        if existing:
            return str(existing.get("_id") or entity_key)

        result = await db["companies"].insert_one({
            "entity_key": entity_key,
            "name": name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        return str(result.inserted_id)
    except Exception as e:
        print(f"[get_or_create_company] Error: {e}")
        return entity_key


# ─────────────────────────────────────────────────────────────────────────────
# RELATIONSHIPS
# ─────────────────────────────────────────────────────────────────────────────

async def add_relationship(payload: dict) -> tuple[str, bool]:
    """Add a relationship between entities. Returns (id, created) where created=True if new."""
    db = await get_db()

    source_id = str(payload.get("source_id") or "").strip()
    target_id = str(payload.get("target_id") or "").strip()
    role_type = str(payload.get("role_type") or payload.get("relationship") or "related").strip()

    if not source_id or not target_id:
        raise ValueError("source_id and target_id are required")

    unique_key = f"{source_id}_{target_id}_{role_type}"

    payload["unique_key"] = unique_key
    payload["updated_at"] = datetime.utcnow()

    if "_id" not in payload:
        payload["created_at"] = datetime.utcnow()

    try:
        result = await db["relationships"].update_one(
            {"unique_key": unique_key},
            {"$set": payload},
            upsert=True,
        )

        created = result.upserted_id is not None
        rel_id = str(result.upserted_id or unique_key)

        return rel_id, created
    except DuplicateKeyError:
        # Already exists
        return unique_key, False
    except Exception as e:
        print(f"[add_relationship] Error: {e}")
        return unique_key, False


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH DATA
# ─────────────────────────────────────────────────────────────────────────────

async def get_graph_data() -> dict:
    """Get graph data: nodes (projects, companies, contacts) and links (relationships)."""
    db = await get_db()

    nodes = []
    links = []
    node_ids = set()

    try:
        def _as_list(value) -> list[str]:
            if isinstance(value, list):
                return [str(v).strip() for v in value if str(v).strip()]
            if isinstance(value, str) and value.strip():
                return [value.strip()]
            return []

        project_alias: dict[str, str] = {}
        company_alias: dict[str, str] = {}
        contact_alias: dict[str, str] = {}

        def _register_company_alias(key: str, company_id: str) -> None:
            k = str(key or "").strip()
            if not k:
                return
            company_alias[k] = company_id
            company_alias[k.lower()] = company_id

        # Project nodes (primary business graph roots)
        projects = await db["projects"].find({}).limit(500).to_list(500)
        for proj in projects:
            proj_id = str(proj.get("code") or proj.get("entity_key") or proj.get("_id") or "").strip()
            if not proj_id:
                continue

            nodes.append(
                {
                    "id": proj_id,
                    "name": str(proj.get("name") or proj_id),
                    "type": "project",
                    "color": "#6366F1",
                    "size": 6 if (proj.get("value_billion_vnd") or 0) > 100 else 4,
                    "province": str(proj.get("province") or ""),
                }
            )
            node_ids.add(proj_id)

            for key in (
                str(proj.get("_id") or "").strip(),
                str(proj.get("entity_key") or "").strip(),
                str(proj.get("code") or "").strip(),
            ):
                if key:
                    project_alias[key] = proj_id

        # Explicit company nodes from companies collection
        companies = await db["companies"].find({}).limit(1500).to_list(1500)
        for comp in companies:
            raw_id = str(comp.get("_id") or "").strip()
            entity_key = str(comp.get("entity_key") or "").strip()
            name = str(comp.get("name") or entity_key or raw_id).strip()
            company_id = entity_key or raw_id or f"co-{_slugify(name)}"

            if company_id not in node_ids:
                nodes.append(
                    {
                        "id": company_id,
                        "name": name,
                        "type": "company",
                        "color": "#F59E0B",
                        "size": 5,
                    }
                )
                node_ids.add(company_id)

            _register_company_alias(raw_id, company_id)
            _register_company_alias(entity_key, company_id)
            _register_company_alias(_slugify(name), company_id)
            _register_company_alias(name, company_id)

        # Contact nodes (hidden by default)
        contacts = await db["contacts"].find({}).limit(2000).to_list(2000)
        for contact in contacts:
            contact_id = str(contact.get("entity_key") or contact.get("_id") or "").strip()
            if not contact_id:
                continue

            nodes.append(
                {
                    "id": contact_id,
                    "name": str(contact.get("full_name") or contact.get("name") or contact_id),
                    "type": "person",
                    "color": "#10B981",
                    "size": 3,
                    "hidden": True,
                    "company": str(contact.get("company") or ""),
                    "role": str(contact.get("role") or ""),
                    "phone": str(contact.get("phone") or ""),
                    "email": str(contact.get("email") or ""),
                }
            )
            node_ids.add(contact_id)

            for key in (
                str(contact.get("_id") or "").strip(),
                str(contact.get("entity_key") or "").strip(),
                str(contact.get("phone") or "").strip(),
                str(contact.get("email") or "").strip(),
            ):
                if key:
                    contact_alias[key] = contact_id

        link_seen: set[tuple[str, str, str]] = set()

        def _add_link(source: str, target: str, rel_type: str, hidden: bool = False) -> None:
            if not source or not target:
                return
            if source not in node_ids or target not in node_ids:
                return
            key = (source, target, rel_type)
            if key in link_seen:
                return
            link_seen.add(key)
            payload = {"source": source, "target": target, "type": rel_type}
            if hidden:
                payload["hidden"] = True
            links.append(payload)

        # Primary fallback: derive project -> company ownership directly from project.developer.
        for proj in projects:
            proj_node_id = project_alias.get(str(proj.get("_id") or "").strip())
            if not proj_node_id:
                continue

            for developer_name in _as_list(proj.get("developer") or []):
                dev_slug = _slugify(developer_name)
                company_id = (
                    company_alias.get(dev_slug)
                    or company_alias.get(developer_name)
                    or company_alias.get(developer_name.lower())
                )

                if not company_id:
                    company_id = f"co-{dev_slug}"
                    if company_id not in node_ids:
                        nodes.append(
                            {
                                "id": company_id,
                                "name": developer_name,
                                "type": "company",
                                "color": "#F59E0B",
                                "size": 5,
                            }
                        )
                        node_ids.add(company_id)

                    _register_company_alias(dev_slug, company_id)
                    _register_company_alias(developer_name, company_id)

                _add_link(proj_node_id, company_id, "owner")

        # Overlay explicit relationships collection with robust id normalization.
        relationships = await db["relationships"].find({}).limit(20000).to_list(20000)

        def _resolve_node_id(raw_id: str) -> str:
            rid = str(raw_id or "").strip()
            if not rid:
                return ""
            if rid in node_ids:
                return rid
            if rid in project_alias:
                return project_alias[rid]
            if rid in contact_alias:
                return contact_alias[rid]
            if rid in company_alias:
                return company_alias[rid]
            if rid.lower() in company_alias:
                return company_alias[rid.lower()]
            return ""

        for rel in relationships:
            source = _resolve_node_id(rel.get("source_id"))
            target = _resolve_node_id(rel.get("target_id"))
            role = str(rel.get("role_type") or rel.get("relationship") or "related").strip() or "related"

            # Best-effort company fallback when relationship points to unmapped company-like id.
            if source and not target:
                target_raw = str(rel.get("target_id") or "").strip()
                if target_raw:
                    fallback_company_id = f"co-{_slugify(target_raw)}"
                    if fallback_company_id not in node_ids:
                        nodes.append(
                            {
                                "id": fallback_company_id,
                                "name": target_raw.replace("-", " "),
                                "type": "company",
                                "color": "#F59E0B",
                                "size": 5,
                            }
                        )
                        node_ids.add(fallback_company_id)
                    _register_company_alias(target_raw, fallback_company_id)
                    target = fallback_company_id

            _add_link(source, target, role)

        # Optional hidden contact->company links for detail mode (only when company node exists).
        for contact in contacts:
            contact_id = contact_alias.get(str(contact.get("entity_key") or "").strip()) or contact_alias.get(
                str(contact.get("_id") or "").strip()
            )
            if not contact_id:
                continue

            company_name = str(contact.get("company") or "").strip()
            if not company_name:
                continue

            company_id = (
                company_alias.get(company_name)
                or company_alias.get(company_name.lower())
                or company_alias.get(_slugify(company_name))
            )
            if company_id:
                _add_link(contact_id, company_id, "works_at", hidden=True)

        return {"nodes": nodes, "links": links}

    except Exception as e:
        print(f"[get_graph_data] Error: {e}")
        return {"nodes": [], "links": []}


# ─────────────────────────────────────────────────────────────────────────────
# STATISTICS
# ─────────────────────────────────────────────────────────────────────────────

async def get_stats() -> dict:
    """Get comprehensive statistics about the database."""
    db = await get_db()

    try:
        # Basic counts
        projects_count = await db["projects"].count_documents({})
        contacts_count = await db["contacts"].count_documents({})
        companies_count = await db["companies"].count_documents({})
        relationships_count = await db["relationships"].count_documents({})

        # Total value in billion VND
        total_value_pipeline = [
            {"$group": {"_id": None, "total": {"$sum": "$value_billion_vnd"}}}
        ]
        value_result = await db["projects"].aggregate(total_value_pipeline).to_list(1)
        total_value_billion_vnd = value_result[0]["total"] if value_result else 0

        # Projects by province
        province_pipeline = [
            {"$group": {"_id": "$province", "count": {"$sum": 1}}},
            {"$match": {"_id": {"$ne": None, "$ne": ""}}},
            {"$sort": {"count": -1}},
        ]
        provinces = await db["projects"].aggregate(province_pipeline).to_list(100)

        # Project value by status
        status_pipeline = [
            {"$group": {"_id": "$status", "total_value": {"$sum": "$value_billion_vnd"}, "count": {"$sum": 1}}},
            {"$match": {"_id": {"$ne": None, "$ne": ""}}},
            {"$sort": {"total_value": -1}},
        ]
        statuses = await db["projects"].aggregate(status_pipeline).to_list(100)

        return {
            "counts": {
                "projects": projects_count,
                "contacts": contacts_count,
                "companies": companies_count,
                "relationships": relationships_count,
            },
            "project_value_total_billion_vnd": total_value_billion_vnd,
            "projects_by_province": [
                {"province": item["_id"], "count": item["count"]}
                for item in provinces
            ],
            "project_value_by_status": [
                {"status": item["_id"], "total_value": item["total_value"], "count": item["count"]}
                for item in statuses
            ],
        }

    except Exception as e:
        print(f"[get_stats] Error: {e}")
        return {
            "counts": {"projects": 0, "contacts": 0, "companies": 0, "relationships": 0},
            "project_value_total_billion_vnd": 0,
            "projects_by_province": [],
            "project_value_by_status": [],
        }


# ─────────────────────────────────────────────────────────────────────────────
# QUERY LOGS
# ─────────────────────────────────────────────────────────────────────────────

async def save_query_log(query: str, answer: str, intent: str = "lookup") -> None:
    """Save a query and its answer to the log."""
    db = await get_db()

    try:
        await db["query_logs"].insert_one({
            "query": query,
            "answer": answer,
            "intent": intent,
            "created_at": datetime.utcnow(),
        })
    except Exception as e:
        print(f"[save_query_log] Error: {e}")


def _serialize_value(value):
    """Convert MongoDB values into JSON-serializable data."""
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize_value(item) for item in value]
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _serialize_doc(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable dict."""
    out = {}
    for k, v in doc.items():
        if k == "_id":
            out["id"] = str(v)
        else:
            out[k] = _serialize_value(v)
    return out


async def get_query_history(limit: int = 30) -> list[dict]:
    """Get recent query history."""
    db = await get_db()

    try:
        logs = (
            await db["query_logs"]
            .find({})
            .sort("created_at", -1)
            .limit(limit)
            .to_list(limit)
        )
        return [_serialize_doc(doc) for doc in (logs or [])]
    except Exception as e:
        print(f"[get_query_history] Error: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# CRUD HELPERS — used by the AI mutation endpoint
# ─────────────────────────────────────────────────────────────────────────────

async def delete_project(entity_key: str) -> bool:
    """Delete a project by entity_key or code."""
    db = await get_db()
    try:
        result = await db["projects"].delete_one(_project_identity_filter(entity_key))
        return result.deleted_count > 0
    except Exception as e:
        print(f"[delete_project] Error: {e}")
        return False


async def delete_contact(entity_key: str) -> bool:
    """Delete a contact by entity_key."""
    db = await get_db()
    try:
        result = await db["contacts"].delete_one(_contact_identity_filter(entity_key))
        return result.deleted_count > 0
    except Exception as e:
        print(f"[delete_contact] Error: {e}")
        return False


async def update_project_fields(entity_key: str, updates: dict) -> bool:
    """Partially update a project — only the supplied fields."""
    db = await get_db()
    try:
        safe = {k: v for k, v in updates.items() if k not in ("_id", "entity_key", "created_at")}
        safe["updated_at"] = datetime.utcnow()
        result = await db["projects"].update_one(
            _project_identity_filter(entity_key),
            {"$set": safe},
        )
        return result.matched_count > 0
    except Exception as e:
        print(f"[update_project_fields] Error: {e}")
        return False


async def update_contact_fields(entity_key: str, updates: dict) -> bool:
    """Partially update a contact — only the supplied fields."""
    db = await get_db()
    try:
        safe = {k: v for k, v in updates.items() if k not in ("_id", "entity_key", "created_at")}
        safe["updated_at"] = datetime.utcnow()
        result = await db["contacts"].update_one(
            _contact_identity_filter(entity_key),
            {"$set": safe},
        )
        return result.matched_count > 0
    except Exception as e:
        print(f"[update_contact_fields] Error: {e}")
        return False


async def find_project_by_name(name: str) -> Optional[dict]:
    """Find a project by approximate name match."""
    db = await get_db()
    try:
        # Try exact first
        doc = await db["projects"].find_one({"name": {"$regex": re.escape(name), "$options": "i"}})
        if doc:
            return doc
        # Fallback: text search
        results = await db["projects"].find({"$text": {"$search": name}}).limit(1).to_list(1)
        return results[0] if results else None
    except Exception as e:
        print(f"[find_project_by_name] Error: {e}")
        return None


async def find_contact_by_name(name: str) -> Optional[dict]:
    """Find a contact by approximate name match."""
    db = await get_db()
    try:
        doc = await db["contacts"].find_one({"full_name": {"$regex": re.escape(name), "$options": "i"}})
        if doc:
            return doc
        results = await db["contacts"].find({"$text": {"$search": name}}).limit(1).to_list(1)
        return results[0] if results else None
    except Exception as e:
        print(f"[find_contact_by_name] Error: {e}")
        return None


async def delete_query_log(log_id: str) -> bool:
    """Delete a single query log by its id."""
    db = await get_db()
    try:
        result = await db["query_logs"].delete_one({"_id": ObjectId(log_id)})
        return result.deleted_count > 0
    except Exception as e:
        print(f"[delete_query_log] Error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# CHAT SESSIONS
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_chat_message(item: dict) -> dict | None:
    """Normalize a chat message payload for storage."""
    role = str(item.get("role") or "user").strip().lower()
    role = "ai" if role in {"assistant", "ai", "model"} else "user"

    content = str(item.get("content") or "").strip()
    if not content:
        return None

    out = {
        "role": role,
        "content": content[:8000],
    }

    citations = item.get("citations")
    if isinstance(citations, list) and citations:
        out["citations"] = [_serialize_value(c) for c in citations[:20]]

    context_used = item.get("context_used")
    if isinstance(context_used, (int, float)):
        out["context_used"] = int(context_used)

    graph_filter = item.get("graph_filter")
    if isinstance(graph_filter, dict):
        out["graph_filter"] = _serialize_value(graph_filter)

    return out


async def save_chat_session(
    messages: list[dict],
    title: str = "",
    session_id: str | None = None,
) -> str:
    """Upsert a full chat session. Returns session id."""
    db = await get_db()

    normalized_messages: list[dict] = []
    for item in (messages or [])[-200:]:
        if not isinstance(item, dict):
            continue
        normalized = _normalize_chat_message(item)
        if normalized:
            normalized_messages.append(normalized)

    if not normalized_messages:
        return ""

    resolved_title = str(title or "").strip()
    if not resolved_title:
        first_user = next(
            (m.get("content", "") for m in normalized_messages if m.get("role") == "user"),
            normalized_messages[0].get("content", ""),
        )
        resolved_title = first_user[:80]

    now = datetime.utcnow()
    payload = {
        "title": resolved_title[:160],
        "messages": normalized_messages,
        "updated_at": now,
    }

    if session_id:
        try:
            oid = ObjectId(session_id)
            result = await db["chat_sessions"].update_one(
                {"_id": oid},
                {"$set": payload},
            )
            if result.matched_count > 0:
                return session_id
        except Exception:
            pass

    payload["created_at"] = now
    result = await db["chat_sessions"].insert_one(payload)
    return str(result.inserted_id)


async def get_chat_sessions(limit: int = 30) -> list[dict]:
    """Get recent chat sessions (summaries only)."""
    db = await get_db()
    try:
        sessions = (
            await db["chat_sessions"]
            .find({}, {"title": 1, "created_at": 1, "updated_at": 1, "messages": 1})
            .sort("updated_at", -1)
            .limit(limit)
            .to_list(limit)
        )

        out: list[dict] = []
        for s in sessions or []:
            out.append(
                {
                    "id": str(s.get("_id")),
                    "title": str(s.get("title") or "Cuộc trò chuyện"),
                    "created_at": _serialize_value(s.get("created_at")),
                    "updated_at": _serialize_value(s.get("updated_at")),
                    "message_count": len(s.get("messages") or []),
                }
            )
        return out
    except Exception as e:
        print(f"[get_chat_sessions] Error: {e}")
        return []


async def get_chat_session(session_id: str) -> dict | None:
    """Get a full chat session by id."""
    db = await get_db()
    try:
        doc = await db["chat_sessions"].find_one({"_id": ObjectId(session_id)})
        if not doc:
            return None
        serialized = _serialize_doc(doc)
        serialized["title"] = str(serialized.get("title") or "Cuộc trò chuyện")
        serialized["messages"] = serialized.get("messages") or []
        return serialized
    except Exception as e:
        print(f"[get_chat_session] Error: {e}")
        return None


async def delete_chat_session(session_id: str) -> bool:
    """Delete a chat session by id."""
    db = await get_db()
    try:
        result = await db["chat_sessions"].delete_one({"_id": ObjectId(session_id)})
        return result.deleted_count > 0
    except Exception as e:
        print(f"[delete_chat_session] Error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────────────────────────────────────

async def save_report(title: str, file_path: str, query: str = "") -> str:
    """Save a report reference. Returns report id."""
    db = await get_db()

    try:
        result = await db["reports"].insert_one({
            "title": title,
            "file_path": file_path,
            "query": query,
            "created_at": datetime.utcnow(),
        })
        return str(result.inserted_id)
    except Exception as e:
        print(f"[save_report] Error: {e}")
        return ""


async def get_reports() -> list[dict]:
    """Get all saved reports."""
    db = await get_db()

    try:
        reports = (
            await db["reports"]
            .find({})
            .sort("created_at", -1)
            .to_list(1000)
        )
        return [_serialize_doc(doc) for doc in (reports or [])]
    except Exception as e:
        print(f"[get_reports] Error: {e}")
        return []
        contacts_count = await db["contacts"].count_documents({})
        companies_count = await db["companies"].count_documents({})
        relationships_count = await db["relationships"].count_documents({})

        total_value_pipeline = [
            {"$group": {"_id": None, "total": {"$sum": "$value_billion_vnd"}}}
        ]
        value_result = await db["projects"].aggregate(total_value_pipeline).to_list(1)
        total_value_billion_vnd = value_result[0]["total"] if value_result else 0

        province_pipeline = [
            {"$group": {"_id": "$province", "count": {"$sum": 1}}},
            {"$match": {"_id": {"$ne": None, "$ne": ""}}},
            {"$sort": {"count": -1}},
        ]
        provinces = await db["projects"].aggregate(province_pipeline).to_list(100)

        status_pipeline = [
            {"$group": {"_id": "$status", "total_value": {"$sum": "$value_billion_vnd"}, "count": {"$sum": 1}}},
            {"$match": {"_id": {"$ne": None, "$ne": ""}}},
            {"$sort": {"total_value": -1}},
        ]
        statuses = await db["projects"].aggregate(status_pipeline).to_list(100)

        return {
            "counts": {
                "projects": projects_count,
                "contacts": contacts_count,
                "companies": companies_count,
                "relationships": relationships_count,
            },
            "project_value_total_billion_vnd": total_value_billion_vnd,
            "projects_by_province": [
                {"province": item["_id"], "count": item["count"]}
                for item in provinces
            ],
            "project_value_by_status": [
                {"status": item["_id"], "total_value": item["total_value"], "count": item["count"]}
                for item in statuses
            ],
        }

    except Exception as e:
        print(f"[get_stats] Error: {e}")
        return {
            "counts": {"projects": 0, "contacts": 0, "companies": 0, "relationships": 0},
            "project_value_total_billion_vnd": 0,
            "projects_by_province": [],
            "project_value_by_status": [],
        }


# ─────────────────────────────────────────────────────────────────────────────
# CRUD HELPERS — used by the AI mutation endpoint
# ─────────────────────────────────────────────────────────────────────────────

async def delete_project(entity_key: str) -> bool:
    """Delete a project by entity_key or code."""
    db = await get_db()
    try:
        result = await db["projects"].delete_one(_project_identity_filter(entity_key))
        return result.deleted_count > 0
    except Exception as e:
        print(f"[delete_project] Error: {e}")
        return False


async def delete_contact(entity_key: str) -> bool:
    """Delete a contact by entity_key."""
    db = await get_db()
    try:
        result = await db["contacts"].delete_one(_contact_identity_filter(entity_key))
        return result.deleted_count > 0
    except Exception as e:
        print(f"[delete_contact] Error: {e}")
        return False


async def update_project_fields(entity_key: str, updates: dict) -> bool:
    """Partially update a project — only the supplied fields."""
    db = await get_db()
    try:
        safe = {k: v for k, v in updates.items() if k not in ("_id", "entity_key", "created_at")}
        safe["updated_at"] = datetime.utcnow()
        result = await db["projects"].update_one(
            _project_identity_filter(entity_key),
            {"$set": safe},
        )
        return result.matched_count > 0
    except Exception as e:
        print(f"[update_project_fields] Error: {e}")
        return False


async def update_contact_fields(entity_key: str, updates: dict) -> bool:
    """Partially update a contact — only the supplied fields."""
    db = await get_db()
    try:
        safe = {k: v for k, v in updates.items() if k not in ("_id", "entity_key", "created_at")}
        safe["updated_at"] = datetime.utcnow()
        result = await db["contacts"].update_one(
            _contact_identity_filter(entity_key),
            {"$set": safe},
        )
        return result.matched_count > 0
    except Exception as e:
        print(f"[update_contact_fields] Error: {e}")
        return False


async def find_project_by_name(name: str) -> Optional[dict]:
    """Find a project by approximate name match."""
    db = await get_db()
    try:
        doc = await db["projects"].find_one({"name": {"$regex": re.escape(name), "$options": "i"}})
        if doc:
            return doc
        results = await db["projects"].find({"$text": {"$search": name}}).limit(1).to_list(1)
        return results[0] if results else None
    except Exception as e:
        print(f"[find_project_by_name] Error: {e}")
        return None


async def find_contact_by_name(name: str) -> Optional[dict]:
    """Find a contact by approximate name match."""
    db = await get_db()
    try:
        doc = await db["contacts"].find_one({"full_name": {"$regex": re.escape(name), "$options": "i"}})
        if doc:
            return doc
        results = await db["contacts"].find({"$text": {"$search": name}}).limit(1).to_list(1)
        return results[0] if results else None
    except Exception as e:
        print(f"[find_contact_by_name] Error: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# QUERY LOGS
# ─────────────────────────────────────────────────────────────────────────────

async def save_query_log(query: str, answer: str, intent: str = "lookup") -> None:
    """Save a query and its answer to the log."""
    db = await get_db()
    try:
        await db["query_logs"].insert_one({
            "query": query,
            "answer": answer,
            "intent": intent,
            "created_at": datetime.utcnow(),
        })
    except Exception as e:
        print(f"[save_query_log] Error: {e}")


def _serialize_value(value):
    """Convert MongoDB values into JSON-serializable data."""
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize_value(item) for item in value]
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _serialize_doc(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable dict."""
    out = {}
    for k, v in doc.items():
        if k == "_id":
            out["id"] = str(v)
        else:
            out[k] = _serialize_value(v)
    return out


async def get_query_history(limit: int = 30) -> list[dict]:
    """Get recent query history."""
    db = await get_db()
    try:
        logs = (
            await db["query_logs"]
            .find({})
            .sort("created_at", -1)
            .limit(limit)
            .to_list(limit)
        )
        return [_serialize_doc(doc) for doc in (logs or [])]
    except Exception as e:
        print(f"[get_query_history] Error: {e}")
        return []


async def delete_query_log(log_id: str) -> bool:
    """Delete a single query log by its id."""
    db = await get_db()
    try:
        result = await db["query_logs"].delete_one({"_id": ObjectId(log_id)})
        return result.deleted_count > 0
    except Exception as e:
        print(f"[delete_query_log] Error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# CHAT SESSIONS
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_chat_message(item: dict) -> dict | None:
    """Normalize a chat message payload for storage."""
    role = str(item.get("role") or "user").strip().lower()
    role = "ai" if role in {"assistant", "ai", "model"} else "user"

    content = str(item.get("content") or "").strip()
    if not content:
        return None

    out = {
        "role": role,
        "content": content[:8000],
    }

    citations = item.get("citations")
    if isinstance(citations, list) and citations:
        out["citations"] = [_serialize_value(c) for c in citations[:20]]

    context_used = item.get("context_used")
    if isinstance(context_used, (int, float)):
        out["context_used"] = int(context_used)

    graph_filter = item.get("graph_filter")
    if isinstance(graph_filter, dict):
        out["graph_filter"] = _serialize_value(graph_filter)

    return out


async def save_chat_session(
    messages: list[dict],
    title: str = "",
    session_id: str | None = None,
) -> str:
    """Upsert a full chat session. Returns session id."""
    db = await get_db()

    normalized_messages: list[dict] = []
    for item in (messages or [])[-200:]:
        if not isinstance(item, dict):
            continue
        normalized = _normalize_chat_message(item)
        if normalized:
            normalized_messages.append(normalized)

    if not normalized_messages:
        return ""

    resolved_title = str(title or "").strip()
    if not resolved_title:
        first_user = next(
            (m.get("content", "") for m in normalized_messages if m.get("role") == "user"),
            normalized_messages[0].get("content", ""),
        )
        resolved_title = first_user[:80]

    now = datetime.utcnow()
    payload = {
        "title": resolved_title[:160],
        "messages": normalized_messages,
        "updated_at": now,
    }

    if session_id:
        try:
            oid = ObjectId(session_id)
            result = await db["chat_sessions"].update_one(
                {"_id": oid},
                {"$set": payload},
            )
            if result.matched_count > 0:
                return session_id
        except Exception:
            pass

    payload["created_at"] = now
    result = await db["chat_sessions"].insert_one(payload)
    return str(result.inserted_id)


async def get_chat_sessions(limit: int = 30) -> list[dict]:
    """Get recent chat sessions (summaries only)."""
    db = await get_db()
    try:
        sessions = (
            await db["chat_sessions"]
            .find({}, {"title": 1, "created_at": 1, "updated_at": 1, "messages": 1})
            .sort("updated_at", -1)
            .limit(limit)
            .to_list(limit)
        )

        out: list[dict] = []
        for s in sessions or []:
            out.append(
                {
                    "id": str(s.get("_id")),
                    "title": str(s.get("title") or "Cuộc trò chuyện"),
                    "created_at": _serialize_value(s.get("created_at")),
                    "updated_at": _serialize_value(s.get("updated_at")),
                    "message_count": len(s.get("messages") or []),
                }
            )
        return out
    except Exception as e:
        print(f"[get_chat_sessions] Error: {e}")
        return []


async def get_chat_session(session_id: str) -> dict | None:
    """Get a full chat session by id."""
    db = await get_db()
    try:
        doc = await db["chat_sessions"].find_one({"_id": ObjectId(session_id)})
        if not doc:
            return None
        serialized = _serialize_doc(doc)
        serialized["title"] = str(serialized.get("title") or "Cuộc trò chuyện")
        serialized["messages"] = serialized.get("messages") or []
        return serialized
    except Exception as e:
        print(f"[get_chat_session] Error: {e}")
        return None


async def delete_chat_session(session_id: str) -> bool:
    """Delete a chat session by id."""
    db = await get_db()
    try:
        result = await db["chat_sessions"].delete_one({"_id": ObjectId(session_id)})
        return result.deleted_count > 0
    except Exception as e:
        print(f"[delete_chat_session] Error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────────────────────────────────────

async def save_report(title: str, file_path: str, query: str = "") -> str:
    """Save a report reference. Returns report id."""
    db = await get_db()
    try:
        result = await db["reports"].insert_one({
            "title": title,
            "file_path": file_path,
            "query": query,
            "created_at": datetime.utcnow(),
        })
        return str(result.inserted_id)
    except Exception as e:
        print(f"[save_report] Error: {e}")
        return ""


async def get_reports() -> list[dict]:
    """Get all saved reports."""
    db = await get_db()
    try:
        reports = (
            await db["reports"]
            .find({})
            .sort("created_at", -1)
            .to_list(1000)
        )
        return [_serialize_doc(doc) for doc in (reports or [])]
    except Exception as e:
        print(f"[get_reports] Error: {e}")
        return []


async def get_report(report_id: str) -> dict | None:
    """Get a single saved report by id."""
    db = await get_db()
    try:
        query: dict = {"_id": report_id}
        try:
            query = {"_id": ObjectId(report_id)}
        except Exception:
            pass
        doc = await db["reports"].find_one(query)
        return _serialize_doc(doc) if doc else None
    except Exception as e:
        print(f"[get_report] Error: {e}")
        return None
