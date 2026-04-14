"""API router for forecasting endpoints."""

from fastapi import APIRouter, HTTPException

from app.models import ForecastRequest
from app.services.fred_service import get_series_data
from app.services.forecast_service import auto_forecast
from app.services.dataset_service import get_dataset_series

router = APIRouter()


@router.post("/")
async def forecast(request: ForecastRequest):
    """Generate a forecast for a data series."""
    try:
        # Determine if this is a FRED series or custom dataset
        if request.series_id.startswith("custom_"):
            parts = request.series_id.split("_", 2)
            if len(parts) >= 3:
                dataset_id = parts[1]
                value_col = parts[2]
                # We need date_col info - for now use the stored dataset
                from app.services.dataset_service import get_dataset
                ds = get_dataset(dataset_id)
                if ds and ds.get("date_column"):
                    series_data = get_dataset_series(dataset_id, ds["date_column"], value_col)
                else:
                    raise ValueError("Custom dataset not found or missing date column")
            else:
                raise ValueError("Invalid custom series ID format")
        else:
            series_data = await get_series_data(
                request.series_id, request.start_date, request.end_date
            )

        result = auto_forecast(
            dates=series_data["dates"],
            values=series_data["values"],
            periods=request.periods,
            method=request.method,
            confidence_level=request.confidence_level,
        )

        result["series_id"] = request.series_id
        result["title"] = series_data.get("title", request.series_id)
        result["historical_dates"] = series_data["dates"]
        result["historical_values"] = series_data["values"]

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast error: {str(e)}")
