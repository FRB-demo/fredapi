"""Enum classes for magic strings used throughout the application.

Addresses: B-10 (magic strings throughout).
"""

from enum import Enum


class QueryIntent(str, Enum):
    """Chat query intent types."""
    TREND = "trend"
    COMPARE = "compare"
    FORECAST = "forecast"
    CURRENT = "current"
    EXTREMES = "extremes"
    AVERAGE = "average"
    CORRELATION = "correlation"
    EXPLAIN = "explain"
    RECOMMEND = "recommend"
    GENERAL = "general"


class ForecastMethod(str, Enum):
    """Forecasting method identifiers."""
    AUTO = "auto"
    HOLT_WINTERS = "holt_winters"
    ARIMA = "arima"
    LINEAR = "linear"


class FrequencyCode(str, Enum):
    """Time series frequency codes."""
    BUSINESS_DAILY = "B"
    WEEKLY = "W"
    MONTHLY = "MS"
    QUARTERLY = "QS"
    YEARLY = "YS"
