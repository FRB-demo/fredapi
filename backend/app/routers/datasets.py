"""API router for custom dataset management."""

import logging
import os
import re

from fastapi import APIRouter, HTTPException, UploadFile, File, Query

from app.config import settings
from app.services.dataset_service import (
    parse_upload,
    get_dataset_series,
    list_datasets,
    delete_dataset,
    get_dataset,
)

logger = logging.getLogger("econsight.datasets")

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/octet-stream",
}
SAFE_FILENAME_RE = re.compile(r"^[\w\-. ]+$")

router = APIRouter()


def _sanitize_filename(filename: str) -> str:
    """S-3: Sanitize uploaded filename to prevent path traversal."""
    # Strip directory components
    filename = os.path.basename(filename)
    # Remove any non-safe characters
    name, ext = os.path.splitext(filename)
    name = re.sub(r"[^\w\-. ]", "_", name)
    return f"{name}{ext}"


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload a CSV or Excel file as a new dataset."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # S-3: Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Use CSV or Excel.")

    # S-3: Validate content type
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning("Unexpected content type: %s for file %s", file.content_type, file.filename)

    # S-3: Sanitize filename
    safe_filename = _sanitize_filename(file.filename)

    # S-3: Enforce file size limit
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size_bytes // 1_000_000} MB.",
        )

    try:
        result = parse_upload(content, safe_filename)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Upload processing failed for %s", safe_filename)
        raise HTTPException(status_code=500, detail="Failed to process uploaded file")


@router.get("/")
async def list_all_datasets():
    """List all uploaded datasets."""
    return {"datasets": list_datasets()}


@router.get("/{dataset_id}/series")
async def get_series_from_dataset(
    dataset_id: str,
    date_col: str = Query(...),
    value_col: str = Query(...),
):
    """Extract a time series from an uploaded dataset."""
    try:
        result = get_dataset_series(dataset_id, date_col, value_col)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("Error extracting series from dataset %s", dataset_id)
        raise HTTPException(status_code=500, detail="Failed to extract series")


@router.delete("/{dataset_id}")
async def remove_dataset(dataset_id: str):
    """Delete an uploaded dataset."""
    if delete_dataset(dataset_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Dataset not found")
