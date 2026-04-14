"""API router for custom dataset management."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query

from app.services.dataset_service import (
    parse_upload,
    get_dataset_series,
    list_datasets,
    delete_dataset,
    get_dataset,
)

router = APIRouter()


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload a CSV or Excel file as a new dataset."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    try:
        result = parse_upload(content, file.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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


@router.delete("/{dataset_id}")
async def remove_dataset(dataset_id: str):
    """Delete an uploaded dataset."""
    if delete_dataset(dataset_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Dataset not found")
