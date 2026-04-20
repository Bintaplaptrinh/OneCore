"""LeadsMap Ingestion Pipeline v2
Flow: Input -> OCR/Parse -> Normalize -> Deduplicate -> Entity Link -> MongoDB
"""
import os
import base64
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import fitz  # PyMuPDF

from core.ai_client import get_ai_client
from core.normalizer import normalize_project_name, normalize_entity_for_upsert, slugify, normalize_phone
from core.deduplicator import find_duplicate_project, find_duplicate_contact, find_duplicate_company
from core.entity_linker import link_entities_for_project, link_entities_for_contact
from core.database import upsert_project, upsert_contact, upsert_company, add_relationship

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".pdf", ".png", ".jpg", ".jpeg", ".webp"}

OCR_SYSTEM_PROMPT = """Bạn là hệ thống OCR và trích xuất thông tin bất động sản.
Phân tích nội dung và trích xuất thành JSON với cấu trúc sau:
{
  "type": "project" | "contact" | "company" | "mixed",
  "projects": [{name, province, district, address, developer, value_billion_vnd, status, build_type, category, floors, area_sqm, start_date, end_date, description}],
  "contacts": [{full_name, company, role, phone, email, address}],
  "companies": [{name, address, phone, email}],
  "relationships": [{contact_name, project_name, company_name, role_type}]
}
Chỉ trả về JSON thuần túy, không giải thích thêm."""


async def parse_image_ocr(file_path: Path) -> dict:
    """Use Gemma4 multimodal OCR on namecard/document images."""
    ai = get_ai_client()

    with open(file_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    suffix = file_path.suffix.lower().lstrip(".")
    mime_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp"
    }
    mime = mime_map.get(suffix, "image/jpeg")

    try:
        response = await ai.chat([{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": OCR_SYSTEM_PROMPT + "\n\nHãy trích xuất thông tin từ ảnh này:"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64,{image_data}"
                    }
                }
            ]
        }], temperature=0.1)

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return parsed
        return {"type": "contact", "contacts": [], "projects": [], "companies": [], "relationships": []}

    except Exception as e:
        print(f"[parse_image_ocr] Error: {e}")
        return {"type": "contact", "contacts": [], "projects": [], "companies": [], "relationships": []}


async def parse_pdf_content(file_path: Path) -> dict:
    """Extract text from PDF, then use Gemma4 to parse entities."""
    try:
        doc = fitz.open(str(file_path))
        text = "\n".join(page.get_text() for page in doc)
        doc.close()

        if not text or not text.strip():
            return {"type": "mixed", "contacts": [], "projects": [], "companies": [], "relationships": []}

        ai = get_ai_client()

        # Truncate text to avoid token limits
        text = text[:8000]

        response = await ai.chat([{
            "role": "user",
            "content": OCR_SYSTEM_PROMPT + f"\n\nNội dung tài liệu:\n{text}"
        }], temperature=0.1)

        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return parsed
        return {"type": "mixed", "contacts": [], "projects": [], "companies": [], "relationships": []}

    except Exception as e:
        print(f"[parse_pdf_content] Error: {e}")
        return {"type": "mixed", "contacts": [], "projects": [], "companies": [], "relationships": []}


def parse_excel(file_path: Path) -> dict:
    """Parse Excel/CSV structured data."""
    try:
        # Try to read with pandas
        if file_path.suffix.lower() in {".csv"}:
            df = pd.read_csv(file_path, dtype=str)
        else:
            df = pd.read_excel(file_path, dtype=str)

        if df.empty:
            return {"type": "mixed", "contacts": [], "projects": [], "companies": [], "relationships": []}

        # Detect entity type from columns
        columns_lower = {col.lower() for col in df.columns}

        is_project = any(col in columns_lower for col in {"name", "project", "tên dự án"})
        is_contact = any(col in columns_lower for col in {"full_name", "name", "phone", "email", "họ tên"})

        projects = []
        contacts = []
        companies = []

        # Map projects
        if is_project:
            for _, row in df.iterrows():
                proj = {
                    "name": str(row.get("name", row.get("Tên dự án", ""))) or "",
                    "province": str(row.get("province", row.get("Tỉnh", ""))) or "",
                    "district": str(row.get("district", row.get("Quận", ""))) or "",
                    "address": str(row.get("address", row.get("Địa chỉ", ""))) or "",
                    "developer": str(row.get("developer", row.get("Chủ đầu tư", ""))) or "",
                    "status": str(row.get("status", row.get("Trạng thái", ""))) or "",
                    "category": str(row.get("category", row.get("Loại", ""))) or "",
                    "area_sqm": str(row.get("area_sqm", row.get("Diện tích", ""))) or "",
                    "floors": str(row.get("floors", row.get("Tầng", ""))) or "",
                }
                if proj.get("name"):
                    projects.append(proj)

        # Map contacts
        if is_contact:
            for _, row in df.iterrows():
                contact = {
                    "full_name": str(row.get("full_name", row.get("name", row.get("Họ tên", "")))) or "",
                    "company": str(row.get("company", row.get("Công ty", ""))) or "",
                    "role": str(row.get("role", row.get("Chức vụ", ""))) or "",
                    "phone": str(row.get("phone", row.get("Số điện thoại", ""))) or "",
                    "email": str(row.get("email", row.get("Email", ""))) or "",
                    "address": str(row.get("address", row.get("Địa chỉ", ""))) or "",
                }
                if contact.get("full_name") or contact.get("phone") or contact.get("email"):
                    contacts.append(contact)

        return {
            "type": "project" if is_project else "contact" if is_contact else "mixed",
            "projects": projects,
            "contacts": contacts,
            "companies": companies,
            "relationships": []
        }

    except Exception as e:
        print(f"[parse_excel] Error: {e}")
        return {"type": "mixed", "contacts": [], "projects": [], "companies": [], "relationships": []}


async def parse_file(file_path: Path) -> dict:
    """Route file to correct parser."""
    ext = file_path.suffix.lower()

    if ext in {".png", ".jpg", ".jpeg", ".webp"}:
        return await parse_image_ocr(file_path)
    elif ext == ".pdf":
        return await parse_pdf_content(file_path)
    elif ext in {".xlsx", ".xls", ".csv"}:
        return parse_excel(file_path)
    else:
        raise ValueError(f"Unsupported: {ext}")


async def ingest_parsed_data(parsed: dict) -> dict:
    """
    Take parsed entity dict, run through normalize->dedup->link->store pipeline.
    Returns {contacts_added, projects_added, companies_added, relationships_added, errors, skipped_duplicates}
    """
    result = {
        "contacts_added": 0,
        "projects_added": 0,
        "companies_added": 0,
        "relationships_added": 0,
        "skipped_duplicates": 0,
        "errors": []
    }

    # Process projects
    for proj_data in parsed.get("projects", []):
        try:
            # Normalize
            proj_data = normalize_entity_for_upsert("project", proj_data)

            if not proj_data.get("name"):
                continue

            # Check for duplicate
            duplicate = await find_duplicate_project(
                proj_data.get("name", ""),
                proj_data.get("province", "")
            )

            if duplicate:
                result["skipped_duplicates"] += 1
                continue

            # Upsert project
            proj_id, created = await upsert_project(proj_data)

            if created:
                result["projects_added"] += 1

            # Link to companies
            rel_count = await link_entities_for_project(proj_id, proj_data)
            result["relationships_added"] += rel_count

        except Exception as e:
            result["errors"].append(f"Project error: {e}")

    # Process contacts
    for contact_data in parsed.get("contacts", []):
        try:
            # Normalize
            contact_data = normalize_entity_for_upsert("contact", contact_data)

            if not (contact_data.get("full_name") or contact_data.get("phone") or contact_data.get("email")):
                continue

            # Check for duplicate
            duplicate = await find_duplicate_contact(
                phone=contact_data.get("phone", ""),
                email=contact_data.get("email", ""),
                full_name=contact_data.get("full_name", ""),
                company=contact_data.get("company", "")
            )

            if duplicate:
                result["skipped_duplicates"] += 1
                continue

            # Upsert contact
            contact_id, created = await upsert_contact(contact_data)

            if created:
                result["contacts_added"] += 1

            # Link to company
            rel_count = await link_entities_for_contact(contact_id, contact_data)
            result["relationships_added"] += rel_count

        except Exception as e:
            result["errors"].append(f"Contact error: {e}")

    # Process companies (explicit)
    for company_data in parsed.get("companies", []):
        try:
            # Normalize
            company_data = normalize_entity_for_upsert("company", company_data)

            if not company_data.get("name"):
                continue

            # Check for duplicate
            duplicate = await find_duplicate_company(company_data.get("name", ""))

            if duplicate:
                result["skipped_duplicates"] += 1
                continue

            # Upsert company
            comp_id, created = await upsert_company(company_data)

            if created:
                result["companies_added"] += 1

        except Exception as e:
            result["errors"].append(f"Company error: {e}")

    return result


async def ingest_file(file_path: Path) -> dict:
    """Full pipeline for a single file."""
    parsed = await parse_file(file_path)
    return await ingest_parsed_data(parsed)


async def ingest_folder(root: Path) -> dict:
    """Batch ingest all supported files in folder."""
    result = {
        "contacts_added": 0,
        "projects_added": 0,
        "companies_added": 0,
        "relationships_added": 0,
        "files_processed": 0,
        "files_skipped": 0,
        "errors": []
    }

    if not root.exists() or not root.is_dir():
        result["errors"].append(f"Folder not found: {root}")
        return result

    # Walk through all files
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue

        ext = file_path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            result["files_skipped"] += 1
            continue

        try:
            file_result = await ingest_file(file_path)

            result["contacts_added"] += file_result.get("contacts_added", 0)
            result["projects_added"] += file_result.get("projects_added", 0)
            result["companies_added"] += file_result.get("companies_added", 0)
            result["relationships_added"] += file_result.get("relationships_added", 0)
            result["files_processed"] += 1

            if file_result.get("errors"):
                result["errors"].extend(file_result["errors"])

        except Exception as e:
            result["errors"].append(f"File {file_path.name}: {e}")

    return result


def get_preview_table(parsed: dict) -> dict:
    """
    Convert parsed data into a preview table for the UI.
    Returns {headers: [...], field_keys: [...], rows: [{field: value},...], entity_type: str}
    Rows are dicts keyed by field_keys so the frontend can edit and reconstruct parsed_data.
    """
    entity_type = parsed.get("type", "mixed")

    if entity_type == "project":
        headers   = ["Tên dự án", "Tỉnh", "Quận", "Địa chỉ", "Chủ đầu tư", "Trạng thái", "Tầng", "Diện tích"]
        field_keys = ["name", "province", "district", "address", "developer", "status", "floors", "area_sqm"]
        rows = [
            {
                "name":     str(p.get("name", "") or ""),
                "province": str(p.get("province", "") or ""),
                "district": str(p.get("district", "") or ""),
                "address":  str(p.get("address", "") or ""),
                "developer":str(p.get("developer", "") or ""),
                "status":   str(p.get("status", "") or ""),
                "floors":   str(p.get("floors", "") or ""),
                "area_sqm": str(p.get("area_sqm", "") or ""),
            }
            for p in parsed.get("projects", [])
        ]
        return {"headers": headers, "field_keys": field_keys, "rows": rows, "entity_type": "project"}

    elif entity_type == "contact":
        headers    = ["Họ tên", "Công ty", "Chức vụ", "Số điện thoại", "Email", "Địa chỉ"]
        field_keys = ["full_name", "company", "role", "phone", "email", "address"]
        rows = [
            {
                "full_name": str(c.get("full_name", "") or ""),
                "company":   str(c.get("company", "") or ""),
                "role":      str(c.get("role", "") or ""),
                "phone":     str(c.get("phone", "") or ""),
                "email":     str(c.get("email", "") or ""),
                "address":   str(c.get("address", "") or ""),
            }
            for c in parsed.get("contacts", [])
        ]
        return {"headers": headers, "field_keys": field_keys, "rows": rows, "entity_type": "contact"}

    else:  # mixed
        projects = parsed.get("projects", []) or []
        contacts = parsed.get("contacts", []) or []

        if projects and not contacts:
            headers    = ["Tên dự án", "Tỉnh", "Quận", "Địa chỉ", "Chủ đầu tư", "Trạng thái"]
            field_keys = ["name", "province", "district", "address", "developer", "status"]
            rows = [
                {
                    "name":     str(p.get("name", "") or ""),
                    "province": str(p.get("province", "") or ""),
                    "district": str(p.get("district", "") or ""),
                    "address":  str(p.get("address", "") or ""),
                    "developer":str(p.get("developer", "") or ""),
                    "status":   str(p.get("status", "") or ""),
                }
                for p in projects
            ]

        elif contacts and not projects:
            headers    = ["Họ tên", "Công ty", "Chức vụ", "Số điện thoại", "Email"]
            field_keys = ["full_name", "company", "role", "phone", "email"]
            rows = [
                {
                    "full_name": str(c.get("full_name", "") or ""),
                    "company":   str(c.get("company", "") or ""),
                    "role":      str(c.get("role", "") or ""),
                    "phone":     str(c.get("phone", "") or ""),
                    "email":     str(c.get("email", "") or ""),
                }
                for c in contacts
            ]

        else:
            # Both present — unified view
            headers    = ["Loại", "Tên/Công ty", "Chi tiết", "Liên hệ"]
            field_keys = ["_type", "name", "detail", "contact"]
            rows = []
            for p in projects[:10]:
                rows.append({
                    "_type":   "Dự án",
                    "name":    str(p.get("name", "") or ""),
                    "detail":  f"{p.get('province','')}, {p.get('district','')}".strip(", "),
                    "contact": str(p.get("developer", "") or ""),
                })
            for c in contacts[:10]:
                rows.append({
                    "_type":   "Liên hệ",
                    "name":    str(c.get("full_name", "") or ""),
                    "detail":  str(c.get("company", "") or ""),
                    "contact": str(c.get("phone", "") or ""),
                })

        return {"headers": headers, "field_keys": field_keys, "rows": rows, "entity_type": "mixed"}
