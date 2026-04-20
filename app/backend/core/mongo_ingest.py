"""Ingest files into MongoDB using duantaolao parsers and persistence logic."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from core.duantaolao_bridge import get_ingest_dependencies, init_duantaolao_runtime

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".pdf", ".png", ".jpg", ".jpeg"}


def _entity_text(entity_type: str, data: dict[str, Any]) -> str:
    if entity_type == "contact":
        return " | ".join(
            x
            for x in [
                data.get("full_name"),
                data.get("role"),
                data.get("company"),
                data.get("phone"),
                data.get("email"),
            ]
            if x
        )
    if entity_type == "project":
        return " | ".join(
            x
            for x in [
                data.get("name"),
                data.get("build_type"),
                data.get("province"),
                f"value={data.get('value_billion_vnd')}",
                data.get("status"),
            ]
            if x
        )
    if entity_type == "company":
        return " | ".join(x for x in [data.get("name"), data.get("address"), data.get("phone")] if x)
    return str(data)


async def _parse_file(file_path: Path, deps: dict[str, Any], ai_client: Any) -> Any:
    ext = file_path.suffix.lower()
    if ext in {".csv", ".xlsx", ".xls"}:
        return deps["parse_excel_or_csv"](file_path)
    if ext == ".pdf":
        return await deps["parse_pdf"](file_path, ai_client=ai_client)
    if ext in {".png", ".jpg", ".jpeg"}:
        return await deps["parse_image"](file_path, ai_client=ai_client)
    parsed = deps["parse_excel_or_csv"](file_path)  # never used, keeps same shape if needed
    parsed.errors.append(f"Unsupported file: {file_path.name}")
    return parsed


async def ingest_file(file_path: Path) -> dict[str, Any]:
    await init_duantaolao_runtime()
    deps = get_ingest_dependencies()

    ai_client = deps["FPTAIClient"]()
    try:
        parsed = await _parse_file(file_path, deps, ai_client)
        entities = deps["normalize_entities"](parsed)

        result = {
            "contacts_added": 0,
            "projects_added": 0,
            "companies_added": 0,
            "relationships_added": 0,
            "errors": list(entities.errors),
            "source": str(file_path),
        }

        company_key_to_id: dict[str, str] = {}
        project_key_to_id: dict[str, str] = {}
        contact_key_to_id: dict[str, str] = {}

        for company in entities.companies:
            try:
                payload = company.model_dump(exclude_none=True)
                company_id, created = await deps["upsert_company"](payload)
                if created:
                    result["companies_added"] += 1
                name = payload.get("name")
                if name:
                    company_key_to_id[deps["slugify"](name, separator="")] = company_id
                await deps["add_entity"](
                    "company",
                    company_id,
                    _entity_text("company", payload),
                    {"name": payload.get("name", "")},
                )
            except Exception as exc:  # noqa: BLE001
                result["errors"].append(f"Company persist error ({getattr(company, 'name', '?')}): {exc}")

        for project in entities.projects:
            try:
                payload = project.model_dump(exclude_none=True)
                project_id, created = await deps["upsert_project"](payload)
                if created:
                    result["projects_added"] += 1

                key = deps["slugify"](payload.get("code") or payload.get("name"), separator="")
                if key:
                    project_key_to_id[key] = project_id

                await deps["add_entity"](
                    "project",
                    project_id,
                    _entity_text("project", payload),
                    {
                        "province": payload.get("province", ""),
                        "category": payload.get("category", ""),
                    },
                )
            except Exception as exc:  # noqa: BLE001
                result["errors"].append(f"Project persist error ({getattr(project, 'name', '?')}): {exc}")

        for contact in entities.contacts:
            try:
                payload = contact.model_dump(exclude_none=True)
                contact_id, created = await deps["upsert_contact"](payload)
                if created:
                    result["contacts_added"] += 1

                key = deps["slugify"](payload.get("phone") or payload.get("email") or payload.get("full_name"), separator="")
                if key:
                    contact_key_to_id[key] = contact_id

                await deps["add_entity"](
                    "contact",
                    contact_id,
                    _entity_text("contact", payload),
                    {
                        "company": payload.get("company", ""),
                        "role": payload.get("role", ""),
                    },
                )

                company_name = payload.get("company")
                if company_name:
                    company_key = deps["slugify"](company_name, separator="")
                    company_id = company_key_to_id.get(company_key)
                    if not company_id:
                        company_id, company_created = await deps["upsert_company"]({"name": company_name})
                        company_key_to_id[company_key] = company_id
                        if company_created:
                            result["companies_added"] += 1
                            await deps["add_entity"](
                                "company",
                                company_id,
                                _entity_text("company", {"name": company_name}),
                                {"name": company_name},
                            )

                    _, rel_created = await deps["add_relationship"](
                        {
                            "contact_id": contact_id,
                            "company_id": company_id,
                            "role_type": "works_at",
                        }
                    )
                    if rel_created:
                        result["relationships_added"] += 1
            except Exception as exc:  # noqa: BLE001
                result["errors"].append(f"Contact persist error ({getattr(contact, 'full_name', '?')}): {exc}")

        for rel in entities.relationships:
            payload = rel.model_dump(exclude_none=True)
            try:
                contact_id = payload.get("contact_id")
                project_id = payload.get("project_id")
                company_id = payload.get("company_id")

                if not contact_id and payload.get("contact_name"):
                    contact_id = contact_key_to_id.get(deps["slugify"](payload["contact_name"], separator=""))
                if not project_id and payload.get("project_name"):
                    project_id = project_key_to_id.get(deps["slugify"](payload["project_name"], separator=""))
                if not company_id and payload.get("company_name"):
                    company_id = company_key_to_id.get(deps["slugify"](payload["company_name"], separator=""))

                if sum(1 for x in (contact_id, project_id, company_id) if x) < 2:
                    continue

                _, created = await deps["add_relationship"](
                    {
                        "contact_id": contact_id,
                        "project_id": project_id,
                        "company_id": company_id,
                        "role_type": payload.get("role_type"),
                    }
                )
                if created:
                    result["relationships_added"] += 1
            except Exception as exc:  # noqa: BLE001
                result["errors"].append(
                    "Relationship persist error "
                    f"({payload.get('contact_name')}/{payload.get('project_name')}/{payload.get('company_name')}): {exc}"
                )

        return result
    finally:
        await ai_client.close()


async def ingest_folder(root: Path) -> dict[str, Any]:
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
    summary = {
        "files": len(files),
        "contacts_added": 0,
        "projects_added": 0,
        "companies_added": 0,
        "relationships_added": 0,
        "errors": [],
    }

    for file_path in files:
        result = await ingest_file(file_path)
        summary["contacts_added"] += int(result.get("contacts_added", 0))
        summary["projects_added"] += int(result.get("projects_added", 0))
        summary["companies_added"] += int(result.get("companies_added", 0))
        summary["relationships_added"] += int(result.get("relationships_added", 0))
        summary["errors"].extend(result.get("errors", []))

    return summary