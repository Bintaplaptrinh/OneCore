"""Bridge utilities to reuse the chat and ingest stack from duantaolao."""
from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

_runtime_ready = False
_runtime_error: str | None = None


@lru_cache(maxsize=1)
def _resolve_duantaolao_root() -> Path:
    env_path = os.getenv("DUANTAOLAO_PATH", "").strip()
    if env_path:
        root = Path(env_path).expanduser().resolve()
    else:
        # backend/core -> backend -> app -> akhai -> bds
        root = Path(__file__).resolve().parents[4] / "duantaolao"

    if not (root / "backend").exists():
        raise RuntimeError(f"DUANTAOLAO_PATH invalid: {root}")
    return root


def ensure_duantaolao_on_path() -> Path:
    root = _resolve_duantaolao_root()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root


async def init_duantaolao_runtime() -> None:
    global _runtime_ready, _runtime_error
    if _runtime_ready:
        return
    ensure_duantaolao_on_path()

    try:
        from backend.database import init_db  # type: ignore
        from backend.vector_store import init_vector_store  # type: ignore

        await init_db()
        await init_vector_store()
        _runtime_ready = True
        _runtime_error = None
    except Exception as exc:  # noqa: BLE001
        _runtime_error = str(exc)
        raise RuntimeError(f"Cannot init duantaolao runtime: {exc}") from exc


async def backfill_graph_entities() -> dict[str, int]:
    from bson import ObjectId
    from dotenv import load_dotenv
    from motor.motor_asyncio import AsyncIOMotorClient

    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    duantaolao_root = ensure_duantaolao_on_path()
    load_dotenv(duantaolao_root / ".env", override=False)

    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017").strip()
    mongo_db_name = os.getenv("MONGO_DB_NAME", "leadsmap").strip() or "leadsmap"

    client = AsyncIOMotorClient(
        mongo_uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        maxPoolSize=4,
    )
    try:
        db = client[mongo_db_name]
        await db.command("ping")

        contacts = await db.contacts.find({}, {"company": 1}).to_list(length=5000)
        projects = await db.projects.find({}, {"developer": 1}).to_list(length=5000)

        company_cache: dict[str, ObjectId] = {}
        result = {
            "contacts_processed": len(contacts),
            "projects_processed": len(projects),
            "companies_ensured": 0,
            "relationships_created": 0,
        }

        async def ensure_company(name: str | None) -> ObjectId | None:
            cleaned = " ".join(str(name or "").split()).strip()
            if not cleaned:
                return None
            key = cleaned.casefold()
            company_id = company_cache.get(key)
            if company_id is not None:
                return company_id
            now = __import__("datetime").datetime.utcnow()
            query = {"name": cleaned}
            update = {
                "$set": {"name": cleaned, "updated_at": now},
                "$setOnInsert": {"created_at": now},
            }
            outcome = await db.companies.update_one(query, update, upsert=True)
            if outcome.upserted_id is not None:
                company_id = outcome.upserted_id
                result["companies_ensured"] += 1
            else:
                stored = await db.companies.find_one(query, {"_id": 1})
                company_id = stored["_id"] if stored else None
            if company_id is not None:
                company_cache[key] = company_id
            return company_id

        async def ensure_relationship(payload: dict[str, object]) -> bool:
            now = __import__("datetime").datetime.utcnow()
            query = {
                "contact_id": payload.get("contact_id"),
                "project_id": payload.get("project_id"),
                "company_id": payload.get("company_id"),
                "role_type": payload.get("role_type"),
            }
            update = {
                "$set": {"updated_at": now},
                "$setOnInsert": {**payload, "created_at": now},
            }
            outcome = await db.relationships.update_one(query, update, upsert=True)
            return bool(outcome.upserted_id)

        for contact in contacts:
            contact_id = contact.get("_id")
            company_id = await ensure_company(contact.get("company"))
            if not isinstance(contact_id, ObjectId) or company_id is None:
                continue
            if await ensure_relationship({"contact_id": contact_id, "company_id": company_id, "role_type": "works_at"}):
                result["relationships_created"] += 1

        for project in projects:
            project_id = project.get("_id")
            developers = project.get("developer") or []
            if isinstance(developers, str):
                developers = [developers]
            elif not isinstance(developers, list):
                developers = [developers]
            if not isinstance(project_id, ObjectId):
                continue
            for developer in developers:
                company_id = await ensure_company(developer)
                if company_id is None:
                    continue
                if await ensure_relationship({"project_id": project_id, "company_id": company_id, "role_type": "owner"}):
                    result["relationships_created"] += 1

        return result
    finally:
        client.close()


@lru_cache(maxsize=1)
def get_rag_engine() -> Any:
    ensure_duantaolao_on_path()
    from backend.ai_client import FPTAIClient  # type: ignore
    from backend.query import RAGEngine  # type: ignore

    return RAGEngine(ai_client=FPTAIClient())


async def ask_graph_rag(query: str, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    await init_duantaolao_runtime()
    engine = get_rag_engine()
    return await engine.answer(query, history=history or [])


def get_ingest_dependencies() -> dict[str, Any]:
    ensure_duantaolao_on_path()

    from backend.ai_client import FPTAIClient  # type: ignore
    from backend.ingest import normalize_entities, parse_excel_or_csv, parse_image, parse_pdf  # type: ignore
    from backend.database import add_relationship, upsert_company, upsert_contact, upsert_project  # type: ignore
    from backend.text_utils import slugify  # type: ignore
    from backend.vector_store import add_entity  # type: ignore

    return {
        "FPTAIClient": FPTAIClient,
        "normalize_entities": normalize_entities,
        "parse_excel_or_csv": parse_excel_or_csv,
        "parse_image": parse_image,
        "parse_pdf": parse_pdf,
        "add_relationship": add_relationship,
        "upsert_company": upsert_company,
        "upsert_contact": upsert_contact,
        "upsert_project": upsert_project,
        "slugify": slugify,
        "add_entity": add_entity,
    }

