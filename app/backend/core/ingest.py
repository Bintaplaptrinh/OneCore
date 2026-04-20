"""File ingestion pipeline for CSV, XLSX, PDF, and images. Self-contained implementation."""
import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from core.database import upsert_contact, upsert_project

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".pdf", ".png", ".jpg", ".jpeg"}


async def ingest_file(file_path: Path) -> dict[str, Any]:
    """Ingest a single file into MongoDB.

    Returns a summary of ingested entities.
    """
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}

    suffix = file_path.suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        return {"error": f"Unsupported file type: {suffix}"}

    try:
        if suffix in {".csv", ".xlsx", ".xls"}:
            return await _ingest_tabular(file_path)
        elif suffix == ".pdf":
            return await _ingest_pdf(file_path)
        elif suffix in {".png", ".jpg", ".jpeg"}:
            return await _ingest_image(file_path)
        else:
            return {"error": f"Unknown file type: {suffix}"}

    except Exception as e:
        print(f"[ingest_file] Error: {e}")
        return {"error": str(e)}


async def _ingest_tabular(file_path: Path) -> dict[str, Any]:
    """Ingest CSV or Excel file."""
    try:
        # Read file
        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        if df.empty:
            return {"ingested": 0, "skipped": 0, "error": "Empty file"}

        # Detect entity type by columns
        df_columns = {col.lower().replace(" ", "_") for col in df.columns}

        projects_count = 0
        contacts_count = 0
        skipped = 0

        # Check if it's projects data
        if any(col in df_columns for col in ["name", "province", "developer", "status"]):
            for _, row in df.iterrows():
                try:
                    data = _normalize_project_row(row)
                    if data:
                        _, _ = await upsert_project(data)
                        projects_count += 1
                    else:
                        skipped += 1
                except Exception as e:
                    print(f"[_ingest_tabular] Project row error: {e}")
                    skipped += 1

        # Check if it's contacts data
        if any(col in df_columns for col in ["full_name", "email", "phone", "company"]):
            for _, row in df.iterrows():
                try:
                    data = _normalize_contact_row(row)
                    if data:
                        _, _ = await upsert_contact(data)
                        contacts_count += 1
                    else:
                        skipped += 1
                except Exception as e:
                    print(f"[_ingest_tabular] Contact row error: {e}")
                    skipped += 1

        total_ingested = projects_count + contacts_count

        return {
            "ingested": total_ingested,
            "projects": projects_count,
            "contacts": contacts_count,
            "skipped": skipped,
            "file": file_path.name,
        }

    except Exception as e:
        print(f"[_ingest_tabular] Error: {e}")
        return {"error": str(e)}


async def _ingest_pdf(file_path: Path) -> dict[str, Any]:
    """Ingest PDF file - basic extraction without AI."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        text = "\n".join([page.get_text() for page in doc])
        doc.close()

        # Try to extract tables or structured data
        # For now, just return metadata
        return {
            "ingested": 0,
            "message": f"PDF extracted: {len(text)} characters",
            "file": file_path.name,
        }

    except ImportError:
        return {"error": "PyMuPDF not installed"}
    except Exception as e:
        print(f"[_ingest_pdf] Error: {e}")
        return {"error": str(e)}


async def _ingest_image(file_path: Path) -> dict[str, Any]:
    """Ingest image file - basic metadata extraction."""
    try:
        from PIL import Image

        img = Image.open(file_path)
        width, height = img.size

        return {
            "ingested": 0,
            "message": f"Image: {width}x{height}px",
            "file": file_path.name,
        }

    except ImportError:
        return {"error": "Pillow not installed"}
    except Exception as e:
        print(f"[_ingest_image] Error: {e}")
        return {"error": str(e)}


def _normalize_project_row(row: Any) -> Optional[dict]:
    """Convert DataFrame row to project document."""
    data = {}

    # Normalize column names
    row_dict = {}
    if hasattr(row, "to_dict"):
        row_dict = row.to_dict()
    else:
        row_dict = dict(row)

    # Map common field names
    field_map = {
        "name": ["name", "dự án", "project_name", "project"],
        "code": ["code", "mã", "id"],
        "province": ["province", "tỉnh", "tp", "tỉnh/tp"],
        "district": ["district", "quận", "huyện"],
        "address": ["address", "địa chỉ"],
        "developer": ["developer", "chủ đầu tư", "nhà phát triển"],
        "status": ["status", "trạng thái"],
        "phase": ["phase", "giai đoạn", "design_stage"],
        "build_type": ["build_type", "loại hình"],
        "value_billion_vnd": ["value_billion_vnd", "giá trị", "value"],
        "area_sqm": ["area_sqm", "diện tích", "site_area"],
        "floors": ["floors", "số tầng"],
        "start_date": ["start_date", "khởi công"],
        "end_date": ["end_date", "bàn giao"],
        "description": ["description", "ghi chú", "notes"],
    }

    for normalized_key, possible_keys in field_map.items():
        for possible_key in possible_keys:
            # Case-insensitive search
            for row_key in row_dict.keys():
                if str(row_key).lower().replace(" ", "_") == possible_key.lower().replace(" ", "_"):
                    value = row_dict[row_key]
                    if value and str(value).strip() not in {"", "nan", "none"}:
                        data[normalized_key] = value
                    break

    # Must have at least a name
    if not data.get("name"):
        return None

    return data


def _normalize_contact_row(row: Any) -> Optional[dict]:
    """Convert DataFrame row to contact document."""
    data = {}

    # Normalize column names
    row_dict = {}
    if hasattr(row, "to_dict"):
        row_dict = row.to_dict()
    else:
        row_dict = dict(row)

    # Map common field names
    field_map = {
        "full_name": ["full_name", "name", "họ tên", "tên"],
        "phone": ["phone", "số điện thoại", "phone_number"],
        "email": ["email", "email_address"],
        "company": ["company", "công ty"],
        "role": ["role", "chức vụ", "position"],
        "address": ["address", "địa chỉ"],
    }

    for normalized_key, possible_keys in field_map.items():
        for possible_key in possible_keys:
            for row_key in row_dict.keys():
                if str(row_key).lower().replace(" ", "_") == possible_key.lower().replace(" ", "_"):
                    value = row_dict[row_key]
                    if value and str(value).strip() not in {"", "nan", "none"}:
                        data[normalized_key] = value
                    break

    # Must have at least a name or email or phone
    if not (data.get("full_name") or data.get("email") or data.get("phone")):
        return None

    return data


async def ingest_folder(root_path: Path) -> dict[str, Any]:
    """Scan folder and ingest all supported files."""
    if not root_path.is_dir():
        return {"error": f"Not a directory: {root_path}"}

    total_ingested = 0
    total_skipped = 0
    processed_files = 0
    errors = []

    # Find all supported files
    for file_path in root_path.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        try:
            result = await ingest_file(file_path)
            processed_files += 1

            if result.get("error"):
                errors.append(f"{file_path.name}: {result['error']}")
            else:
                total_ingested += result.get("ingested", 0)
                total_skipped += result.get("skipped", 0)

        except Exception as e:
            print(f"[ingest_folder] File error: {e}")
            errors.append(f"{file_path.name}: {str(e)}")

    return {
        "ok": True,
        "processed_files": processed_files,
        "total_ingested": total_ingested,
        "total_skipped": total_skipped,
        "errors": errors,
        "root": str(root_path),
    }
