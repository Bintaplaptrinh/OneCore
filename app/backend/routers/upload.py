"""File upload and ingestion router with preview support."""
from __future__ import annotations

import os
import re
from pathlib import Path

from core.pipeline import (
    SUPPORTED_EXTENSIONS,
    ingest_file,
    ingest_folder,
    parse_file,
    get_preview_table,
    ingest_parsed_data,
)
from fastapi import APIRouter, Body, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter()

UPLOAD_DIR = Path(
    os.getenv("UPLOAD_DIR", Path(__file__).resolve().parents[1] / "uploads")
).resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(file_name: str) -> str:
    """Sanitize filename."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", file_name)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and ingest a file directly."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {suffix}")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    dest = UPLOAD_DIR / _safe_filename(file.filename)
    dest.write_bytes(content)

    result = await ingest_file(dest)
    return JSONResponse(
        {
            "ok": True,
            "type": suffix.lstrip("."),
            "message": f"Ingested into MongoDB: {file.filename}",
            "result": result,
        }
    )


@router.post("/upload/preview")
async def upload_preview(file: UploadFile = File(...)):
    """Parse file without saving, return preview table for user to edit."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {suffix}")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    # Save temporarily
    dest = UPLOAD_DIR / _safe_filename(f"temp_{file.filename}")
    dest.write_bytes(content)

    try:
        parsed = await parse_file(dest)
        preview = get_preview_table(parsed)

        return JSONResponse({
            "ok": True,
            "type": suffix.lstrip("."),
            "parsed_data": parsed,
            "preview": preview,
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {str(e)}")
    finally:
        # Clean up temp file
        try:
            dest.unlink()
        except Exception:
            pass


@router.post("/upload/confirm")
async def upload_confirm(payload: dict = Body(...)):
    """Accept edited parsed data from UI and save to MongoDB."""
    parsed = payload.get("parsed_data")

    if not parsed:
        raise HTTPException(status_code=400, detail="No parsed_data provided")

    try:
        result = await ingest_parsed_data(parsed)
        return JSONResponse({
            "ok": True,
            "result": result,
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ingest error: {str(e)}")


@router.post("/upload/scan")
async def upload_scan_folder(path: str = ""):
    """Scan a folder and ingest all supported files."""
    root = (
        Path(path).expanduser().resolve()
        if path
        else Path(os.getenv("VAULT_PATH", "")).expanduser().resolve()
    )
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=404, detail=f"Folder not found: {root}")

    summary = await ingest_folder(root)
    return {"ok": True, "path": str(root), "result": summary}
