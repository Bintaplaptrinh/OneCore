"""Auto-link entities and maintain graph consistency."""
from core.database import get_db, add_relationship, upsert_company, get_or_create_company


async def link_contact_to_company(contact_id: str, company_name: str) -> str | None:
    """
    Ensure company exists, create works_at relationship.
    Returns company_id.
    """
    if not contact_id or not company_name:
        return None

    company_name = company_name.strip()
    if not company_name:
        return None

    try:
        # Get or create company
        company_id = await get_or_create_company(company_name)

        # Create relationship
        rel_id, _ = await add_relationship({
            "source_id": contact_id,
            "target_id": company_id,
            "role_type": "works_at",
        })

        return company_id

    except Exception as e:
        print(f"[link_contact_to_company] Error: {e}")
        return None


async def link_project_to_company(project_id: str, developer_name: str) -> str | None:
    """
    Ensure company exists, create owner relationship.
    Returns company_id.
    """
    if not project_id or not developer_name:
        return None

    developer_name = developer_name.strip()
    if not developer_name:
        return None

    try:
        # Get or create company
        company_id = await get_or_create_company(developer_name)

        # Create relationship
        rel_id, _ = await add_relationship({
            "source_id": project_id,
            "target_id": company_id,
            "role_type": "owner",
        })

        return company_id

    except Exception as e:
        print(f"[link_project_to_company] Error: {e}")
        return None


async def link_entities_for_project(project_id: str, project_data: dict) -> int:
    """
    Process project's developer list, create all company links.
    Returns count of relationships created.
    """
    developers = project_data.get("developer", [])
    if isinstance(developers, str):
        developers = [developers]

    if not isinstance(developers, list):
        developers = []

    count = 0
    for dev in developers:
        if dev and str(dev).strip():
            rel_id = await link_project_to_company(project_id, str(dev).strip())
            if rel_id:
                count += 1

    return count


async def link_entities_for_contact(contact_id: str, contact_data: dict) -> int:
    """Process contact's company field, create works_at link."""
    company = contact_data.get("company") or ""

    if not company or not str(company).strip():
        return 0

    company_id = await link_contact_to_company(contact_id, str(company).strip())

    return 1 if company_id else 0


async def verify_graph_consistency() -> dict:
    """
    Check for orphan nodes (entities with no relationships).
    Returns {orphan_projects: int, orphan_contacts: int, total_relationships: int}
    """
    db = await get_db()

    try:
        # Get total relationships
        total_relationships = await db["relationships"].count_documents({})

        # Find projects with no relationships
        related_project_ids = await db["relationships"].distinct("source_id")
        all_project_ids = await db["projects"].distinct("_id")

        orphan_projects = 0
        for proj_id in all_project_ids:
            if str(proj_id) not in [str(r) for r in related_project_ids]:
                orphan_projects += 1

        # Find contacts with no relationships
        related_contact_ids = await db["relationships"].distinct("source_id")
        all_contact_ids = await db["contacts"].distinct("_id")

        orphan_contacts = 0
        for contact_id in all_contact_ids:
            if str(contact_id) not in [str(r) for r in related_contact_ids]:
                orphan_contacts += 1

        return {
            "orphan_projects": orphan_projects,
            "orphan_contacts": orphan_contacts,
            "total_relationships": total_relationships,
        }

    except Exception as e:
        print(f"[verify_graph_consistency] Error: {e}")
        return {
            "orphan_projects": 0,
            "orphan_contacts": 0,
            "total_relationships": 0,
        }
