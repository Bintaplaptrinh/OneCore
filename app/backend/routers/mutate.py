"""Data mutation endpoint — executes confirmed CRUD operations from the AI agent."""
from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class MutateRequest(BaseModel):
    """Confirmed mutation payload sent from the frontend after user approval."""

    operation: str          # insert | update | delete
    entity: str             # project | contact
    slug: str | None = None # entity_key for update/delete
    display_name: str = ""  # human-readable name (fallback search)
    data: dict[str, Any] | None = None
    confirmed: bool = False


class MutateResponse(BaseModel):
    success: bool
    message: str
    entity_key: str | None = None


def _name_candidates(display_name: str) -> list[str]:
    """Generate normalized candidate names for fuzzy matching."""
    raw = str(display_name or "").strip().strip('"\'').strip("_-")
    if not raw:
        return []

    candidates: list[str] = [raw]

    # Drop leading operation/entity phrases.
    cleaned = re.sub(
        r"^(xóa|xoá|sửa|chỉnh sửa|cập nhật|thêm|tạo)\s+(dự án|liên hệ)\s+",
        "",
        raw,
        flags=re.IGNORECASE,
    ).strip(" .,;:!?-_")
    if cleaned:
        candidates.append(cleaned)

    # Drop trailing polite particles.
    polite_trim = re.sub(r"\b(đi|nha|nhé|giúp|giúp tôi|please)\b$", "", cleaned, flags=re.IGNORECASE).strip(" .,;:!?-_")
    if polite_trim:
        candidates.append(polite_trim)

    # Keep only part before owner/developer qualifiers.
    owner_split = re.split(r"\s+của\s+", polite_trim, maxsplit=1, flags=re.IGNORECASE)[0].strip(" .,;:!?-_")
    if owner_split:
        candidates.append(owner_split)

    # Remove entity prefix if still present.
    no_prefix = re.sub(r"^(dự án|liên hệ)\s+", "", owner_split, flags=re.IGNORECASE).strip(" .,;:!?-_")
    if no_prefix:
        candidates.append(no_prefix)

    # Stable de-duplication preserving order.
    out: list[str] = []
    for c in candidates:
        if c and c not in out:
            out.append(c)
    return out


async def _resolve_slug(entity: str, slug: str | None, display_name: str) -> str:
    """Try to resolve entity_key: prefer explicit slug, fallback to name search."""
    from core.database import find_project_by_name, find_contact_by_name

    if slug and slug.strip():
        return slug.strip()

    finder = find_project_by_name if entity == "project" else find_contact_by_name
    for name in _name_candidates(display_name):
        doc = await finder(name)
        if doc:
            return str(doc.get("entity_key") or doc.get("code") or "")
    return ""


@router.post("/mutate/execute", response_model=MutateResponse)
async def mutate_execute(req: MutateRequest):
    """Execute a confirmed data mutation operation."""
    from core.database import (
        delete_contact,
        delete_project,
        get_contact_by_slug,
        get_project_by_slug,
        update_contact_fields,
        update_project_fields,
        upsert_contact,
        upsert_project,
    )

    op = req.operation.lower().strip()
    entity = req.entity.lower().strip()
    data = req.data or {}

    if not req.confirmed:
        raise HTTPException(status_code=400, detail="Mutation requires explicit confirmation")

    if op not in ("insert", "update", "delete"):
        raise HTTPException(status_code=400, detail=f"Invalid operation: {op}")
    if entity not in ("project", "contact"):
        raise HTTPException(status_code=400, detail=f"Invalid entity: {entity}")

    try:
        # ── INSERT ──────────────────────────────────────────────────────────
        if op == "insert":
            if not data:
                return MutateResponse(success=False, message="Không có dữ liệu để thêm.")

            # Normalize list fields
            _normalize_lists(data)

            if entity == "project":
                entity_key, created = await upsert_project(dict(data))
                label = "dự án"
            else:
                entity_key, created = await upsert_contact(dict(data))
                label = "liên hệ"

            action = "Thêm mới" if created else "Cập nhật"
            return MutateResponse(
                success=True,
                message=f"{action} {label} **{req.display_name or entity_key}** thành công.",
                entity_key=entity_key,
            )

        # ── UPDATE ──────────────────────────────────────────────────────────
        elif op == "update":
            slug = await _resolve_slug(entity, req.slug, req.display_name)
            if not slug:
                return MutateResponse(
                    success=False,
                    message=f"Không tìm thấy {'dự án' if entity == 'project' else 'liên hệ'} cần cập nhật.",
                )

            if not data:
                return MutateResponse(success=False, message="Không có trường nào để cập nhật.")

            _normalize_lists(data)

            if entity == "project":
                ok = await update_project_fields(slug, dict(data))
                label = "dự án"
                checker = get_project_by_slug
            else:
                ok = await update_contact_fields(slug, dict(data))
                label = "liên hệ"
                checker = get_contact_by_slug

            if not ok:
                existing = await checker(slug)
                if existing:
                    return MutateResponse(
                        success=False,
                        message=(
                            f"Không thể cập nhật {label} **{req.display_name or slug}**. "
                            "Có thể CSDL đang chặn ghi (ví dụ Atlas quota)."
                        ),
                        entity_key=slug,
                    )
                return MutateResponse(
                    success=False,
                    message=f"Không tìm thấy {label} để cập nhật (ID: {slug}).",
                    entity_key=slug,
                )

            return MutateResponse(
                success=True,
                message=f"Cập nhật {label} **{req.display_name or slug}** thành công.",
                entity_key=slug,
            )

        # ── DELETE ──────────────────────────────────────────────────────────
        elif op == "delete":
            slug = await _resolve_slug(entity, req.slug, req.display_name)
            if not slug:
                return MutateResponse(
                    success=False,
                    message=f"Không tìm thấy {'dự án' if entity == 'project' else 'liên hệ'} cần xóa.",
                )

            if entity == "project":
                ok = await delete_project(slug)
                label = "dự án"
                checker = get_project_by_slug
            else:
                ok = await delete_contact(slug)
                label = "liên hệ"
                checker = get_contact_by_slug

            if not ok:
                existing = await checker(slug)
                if existing:
                    return MutateResponse(
                        success=False,
                        message=(
                            f"Không thể xóa {label} **{req.display_name or slug}**. "
                            "Có thể CSDL đang chặn ghi (ví dụ Atlas quota)."
                        ),
                        entity_key=slug,
                    )
                return MutateResponse(
                    success=False,
                    message=f"Không tìm thấy {label} với ID = {slug}.",
                    entity_key=None,
                )

            return MutateResponse(
                success=True,
                message=f"Đã xóa {label} **{req.display_name or slug}** thành công.",
                entity_key=slug,
            )

    except Exception as e:
        print(f"[mutate_execute] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _normalize_lists(data: dict) -> None:
    """Ensure list fields are actual lists, not comma-separated strings."""
    list_fields = {"developer", "type_tags"}
    for field in list_fields:
        val = data.get(field)
        if isinstance(val, str) and val.strip():
            data[field] = [v.strip() for v in val.split(",") if v.strip()]
        elif val is None:
            pass  # leave as-is
