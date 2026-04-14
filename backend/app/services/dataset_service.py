"""Service for managing user-uploaded datasets."""

import io
import uuid
import pandas as pd
from typing import Optional

# In-memory dataset store (in production, use a database)
_datasets: dict[str, dict] = {}


def parse_upload(file_content: bytes, filename: str) -> dict:
    """Parse an uploaded CSV or Excel file into a dataset."""
    dataset_id = str(uuid.uuid4())[:8]

    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_content))
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(file_content))
    else:
        raise ValueError(f"Unsupported file format: {filename}. Use CSV or Excel.")

    # Auto-detect date columns
    date_col = None
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                pd.to_datetime(df[col].head(5))
                date_col = col
                break
            except Exception:
                continue

    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])
        df = df.sort_values(date_col)

    # Store dataset
    _datasets[dataset_id] = {
        "id": dataset_id,
        "name": filename.rsplit(".", 1)[0],
        "filename": filename,
        "columns": df.columns.tolist(),
        "date_column": date_col,
        "numeric_columns": df.select_dtypes(include="number").columns.tolist(),
        "row_count": len(df),
        "data": df,
    }

    # Build preview
    preview_df = df.head(10).copy()
    for col in preview_df.columns:
        if pd.api.types.is_datetime64_any_dtype(preview_df[col]):
            preview_df[col] = preview_df[col].dt.strftime("%Y-%m-%d")

    return {
        "dataset_id": dataset_id,
        "name": filename.rsplit(".", 1)[0],
        "columns": df.columns.tolist(),
        "date_column": date_col,
        "numeric_columns": df.select_dtypes(include="number").columns.tolist(),
        "row_count": len(df),
        "preview": preview_df.fillna("").to_dict(orient="records"),
    }


def get_dataset(dataset_id: str) -> Optional[dict]:
    """Get a stored dataset by ID."""
    return _datasets.get(dataset_id)


def get_dataset_series(dataset_id: str, date_col: str, value_col: str) -> dict:
    """Extract a time series from a stored dataset."""
    ds = _datasets.get(dataset_id)
    if not ds:
        raise ValueError(f"Dataset {dataset_id} not found")

    df = ds["data"]
    if date_col not in df.columns or value_col not in df.columns:
        raise ValueError(f"Column not found in dataset")

    dates_series = df[date_col]
    if pd.api.types.is_datetime64_any_dtype(dates_series):
        dates = dates_series.dt.strftime("%Y-%m-%d").tolist()
    else:
        dates = dates_series.astype(str).tolist()

    values = df[value_col].astype(float).tolist()

    return {
        "series_id": f"custom_{dataset_id}_{value_col}",
        "title": f"{ds['name']} - {value_col}",
        "units": "",
        "frequency": "Custom",
        "source": "Upload",
        "dates": dates,
        "values": values,
    }


def list_datasets() -> list[dict]:
    """List all stored datasets."""
    result = []
    for ds_id, ds in _datasets.items():
        result.append({
            "dataset_id": ds_id,
            "name": ds["name"],
            "columns": ds["columns"],
            "date_column": ds["date_column"],
            "numeric_columns": ds["numeric_columns"],
            "row_count": ds["row_count"],
        })
    return result


def delete_dataset(dataset_id: str) -> bool:
    """Delete a dataset."""
    if dataset_id in _datasets:
        del _datasets[dataset_id]
        return True
    return False
