"""Forecasting service using statsmodels for time-series forecasting."""

import logging

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from scipy import stats
from typing import Optional

logger = logging.getLogger("econsight.forecast")


def _prepare_series(dates: list[str], values: list[float]) -> pd.Series:
    """Convert date/value lists into a pandas Series with DatetimeIndex."""
    idx = pd.to_datetime(dates)
    series = pd.Series(values, index=idx, dtype=float)
    series = series.sort_index()
    series = series.dropna()
    return series


def _infer_frequency(series: pd.Series) -> str:
    """Infer the frequency of the time series."""
    if len(series) < 3:
        return "MS"
    diffs = pd.Series(series.index).diff().dropna()
    median_diff = diffs.median().days
    if median_diff <= 2:
        return "B"
    elif median_diff <= 8:
        return "W"
    elif median_diff <= 35:
        return "MS"
    elif median_diff <= 100:
        return "QS"
    else:
        return "YS"


def _resample_if_needed(series: pd.Series, freq: str) -> pd.Series:
    """Resample series to regular frequency if needed."""
    try:
        resampled = series.resample(freq).last()
        resampled = resampled.ffill()
        return resampled
    except (ValueError, TypeError):
        logger.debug("Resample failed for freq=%s, using original series", freq)
        return series


def forecast_holt_winters(
    series: pd.Series,
    periods: int,
    confidence_level: float = 0.95,
    seasonal_periods: Optional[int] = None,
) -> dict:
    """Holt-Winters exponential smoothing forecast."""
    freq = _infer_frequency(series)
    series = _resample_if_needed(series, freq)

    if seasonal_periods is None:
        if freq in ("MS", "M"):
            seasonal_periods = 12
        elif freq in ("QS", "Q"):
            seasonal_periods = 4
        elif freq in ("W", "W-SUN"):
            seasonal_periods = 52
        else:
            seasonal_periods = None

    try:
        if seasonal_periods and len(series) >= 2 * seasonal_periods:
            model = ExponentialSmoothing(
                series,
                trend="add",
                seasonal="add",
                seasonal_periods=seasonal_periods,
            )
        else:
            model = ExponentialSmoothing(series, trend="add")

        fitted = model.fit(optimized=True)
        forecast = fitted.forecast(periods)

        # Compute prediction intervals using residual standard error
        residuals = fitted.resid.dropna()
        std_err = residuals.std()
        z_score = stats.norm.ppf((1 + confidence_level) / 2)

        steps = np.arange(1, periods + 1)
        margin = z_score * std_err * np.sqrt(steps / len(series) + 1)

        lower = forecast - margin
        upper = forecast + margin

        return {
            "method": "Holt-Winters",
            "forecast_dates": [d.strftime("%Y-%m-%d") for d in forecast.index],
            "forecast_values": forecast.tolist(),
            "lower_bound": lower.tolist(),
            "upper_bound": upper.tolist(),
            "confidence_level": confidence_level,
        }
    except Exception as e:
        raise ValueError(f"Holt-Winters forecast failed: {str(e)}")


def forecast_arima(
    series: pd.Series,
    periods: int,
    confidence_level: float = 0.95,
    order: tuple = (1, 1, 1),
) -> dict:
    """ARIMA forecast."""
    freq = _infer_frequency(series)
    series = _resample_if_needed(series, freq)

    try:
        model = ARIMA(series, order=order)
        fitted = model.fit()
        forecast_result = fitted.get_forecast(steps=periods)
        forecast_mean = forecast_result.predicted_mean
        conf_int = forecast_result.conf_int(alpha=1 - confidence_level)

        return {
            "method": f"ARIMA{order}",
            "forecast_dates": [d.strftime("%Y-%m-%d") for d in forecast_mean.index],
            "forecast_values": forecast_mean.tolist(),
            "lower_bound": conf_int.iloc[:, 0].tolist(),
            "upper_bound": conf_int.iloc[:, 1].tolist(),
            "confidence_level": confidence_level,
        }
    except Exception as e:
        raise ValueError(f"ARIMA forecast failed: {str(e)}")


def forecast_linear_trend(
    series: pd.Series,
    periods: int,
    confidence_level: float = 0.95,
) -> dict:
    """Simple linear trend forecast."""
    freq = _infer_frequency(series)
    series = _resample_if_needed(series, freq)

    x = np.arange(len(series))
    y = series.values.astype(float)
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    future_x = np.arange(len(series), len(series) + periods)
    forecast_values = slope * future_x + intercept

    # Generate future dates
    last_date = series.index[-1]
    future_dates = pd.date_range(start=last_date, periods=periods + 1, freq=freq)[1:]

    # Prediction intervals
    residuals = y - (slope * x + intercept)
    res_std = residuals.std()
    z_score = stats.norm.ppf((1 + confidence_level) / 2)
    margin = z_score * res_std * np.sqrt(1 + 1 / len(series) + (future_x - x.mean()) ** 2 / ((x - x.mean()) ** 2).sum())

    return {
        "method": "Linear Trend",
        "forecast_dates": [d.strftime("%Y-%m-%d") for d in future_dates],
        "forecast_values": forecast_values.tolist(),
        "lower_bound": (forecast_values - margin).tolist(),
        "upper_bound": (forecast_values + margin).tolist(),
        "confidence_level": confidence_level,
        "r_squared": r_value ** 2,
        "slope": slope,
    }


def auto_forecast(
    dates: list[str],
    values: list[float],
    periods: int = 12,
    method: str = "auto",
    confidence_level: float = 0.95,
) -> dict:
    """Run forecasting with automatic method selection."""
    series = _prepare_series(dates, values)

    if len(series) < 5:
        raise ValueError("Need at least 5 data points to forecast")

    if method == "auto":
        # B-16: Try methods in order and track attempts
        methods = [
            ("holt_winters", lambda: forecast_holt_winters(series, periods, confidence_level)),
            ("arima", lambda: forecast_arima(series, periods, confidence_level)),
            ("linear", lambda: forecast_linear_trend(series, periods, confidence_level)),
        ]
        attempted: list[str] = []
        for name, fn in methods:
            try:
                result = fn()
                result["attempted_methods"] = attempted + [f"{name}: success"]
                return result
            except Exception as e:
                attempted.append(f"{name}: {e}")
                logger.debug("Auto forecast: %s failed: %s", name, e)
                continue
        raise ValueError("All forecasting methods failed")

    if method == "holt_winters":
        return forecast_holt_winters(series, periods, confidence_level)
    elif method == "arima":
        return forecast_arima(series, periods, confidence_level)
    elif method == "linear":
        return forecast_linear_trend(series, periods, confidence_level)
    else:
        raise ValueError(f"Unknown method: {method}. Use 'auto', 'holt_winters', 'arima', or 'linear'.")
