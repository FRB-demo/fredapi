"""
Normalization and composite recession probability computation.

This module handles:
1. Resampling series to a common monthly frequency
2. Normalizing each indicator to a 0-1 scale using historical percentiles
3. Adjusting for risk direction (high vs. low values signaling recession)
4. Computing a weighted composite recession probability score
"""

import numpy as np
import pandas as pd

from dashboard.indicators import RecessionIndicator, normalize_weights


def resample_to_monthly(series: pd.Series, method: str = "last") -> pd.Series:
    """
    Resample a time series to monthly frequency.

    Parameters
    ----------
    series : pd.Series
        Input time series with datetime index.
    method : str
        Aggregation method: 'last', 'mean', 'first'.

    Returns
    -------
    pd.Series
        Monthly-resampled series.
    """
    if series.empty:
        return series

    if method == "last":
        return series.resample("MS").last()
    elif method == "mean":
        return series.resample("MS").mean()
    elif method == "first":
        return series.resample("MS").first()
    else:
        return series.resample("MS").last()


def normalize_percentile(series: pd.Series) -> pd.Series:
    """
    Normalize a series to 0-1 scale using expanding historical percentile rank.

    Each value is ranked against all values up to and including that date,
    producing a percentile score between 0 and 1.

    Parameters
    ----------
    series : pd.Series
        Input time series.

    Returns
    -------
    pd.Series
        Percentile-normalized series (0 to 1).
    """
    if series.empty:
        return series

    return series.expanding(min_periods=1).apply(
        lambda x: np.searchsorted(np.sort(x[:-1]), x[-1]) / max(len(x) - 1, 1)
        if len(x) > 1
        else 0.5,
        raw=True,
    )


def normalize_zscore(series: pd.Series, window: int = 120) -> pd.Series:
    """
    Normalize a series to 0-1 scale using rolling z-score mapped through a sigmoid.

    Parameters
    ----------
    series : pd.Series
        Input time series.
    window : int
        Rolling window size in periods (default 120 months = 10 years).

    Returns
    -------
    pd.Series
        Z-score normalized series mapped to 0-1 via sigmoid.
    """
    if series.empty:
        return series

    rolling_mean = series.expanding(min_periods=12).mean()
    rolling_std = series.expanding(min_periods=12).std()

    # Avoid division by zero
    rolling_std = rolling_std.replace(0, np.nan)

    z = (series - rolling_mean) / rolling_std

    # Map z-score to 0-1 via sigmoid
    normalized = 1 / (1 + np.exp(-z))

    return normalized


def compute_risk_score(
    normalized_series: pd.Series, indicator: RecessionIndicator
) -> pd.Series:
    """
    Convert a normalized (0-1) series into a recession risk score.

    For 'high' risk_direction indicators, higher normalized values mean higher risk.
    For 'low' risk_direction indicators, lower normalized values mean higher risk,
    so we invert the score.

    Parameters
    ----------
    normalized_series : pd.Series
        Percentile-normalized series (0 to 1).
    indicator : RecessionIndicator
        The indicator definition.

    Returns
    -------
    pd.Series
        Risk score (0 = low risk, 1 = high risk).
    """
    if indicator.risk_direction == "high":
        return normalized_series
    else:
        return 1.0 - normalized_series


def compute_composite_probability(
    risk_scores: dict[str, pd.Series],
    indicators: list[RecessionIndicator],
    method: str = "weighted_average",
) -> pd.Series:
    """
    Compute a composite recession probability from individual risk scores.

    Parameters
    ----------
    risk_scores : dict[str, pd.Series]
        Dictionary mapping series_id to risk score Series.
    indicators : list[RecessionIndicator]
        List of indicator definitions.
    method : str
        Aggregation method: 'weighted_average' or 'geometric_mean'.

    Returns
    -------
    pd.Series
        Composite recession probability (0 to 1).
    """
    weights = normalize_weights(indicators)

    # Build a DataFrame of risk scores, aligned by date
    scored_ids = [sid for sid in risk_scores if sid in weights]
    if not scored_ids:
        return pd.Series(dtype=float)

    df = pd.DataFrame({sid: risk_scores[sid] for sid in scored_ids})

    if method == "weighted_average":
        weight_series = pd.Series({sid: weights[sid] for sid in scored_ids})

        # Weighted average, ignoring NaN (re-normalize weights for available data)
        def weighted_avg(row: pd.Series) -> float:
            valid = row.dropna()
            if valid.empty:
                return np.nan
            w = weight_series[valid.index]
            w_sum = w.sum()
            if w_sum == 0:
                return np.nan
            return float((valid * w).sum() / w_sum)

        composite = df.apply(weighted_avg, axis=1)

    elif method == "geometric_mean":
        # Geometric mean of risk scores (clip to avoid log(0))
        df_clipped = df.clip(lower=0.001, upper=0.999)
        log_scores = np.log(df_clipped)
        weight_series = pd.Series({sid: weights[sid] for sid in scored_ids})
        composite = np.exp((log_scores * weight_series).sum(axis=1) / weight_series.sum())

    else:
        raise ValueError(f"Unknown method: {method}")

    return composite


def build_indicator_summary(
    latest_values: dict[str, float],
    risk_scores: dict[str, float],
    indicators: list[RecessionIndicator],
) -> pd.DataFrame:
    """
    Build a summary table of current indicator values and risk signals.

    Parameters
    ----------
    latest_values : dict[str, float]
        Dictionary mapping series_id to the latest raw value.
    risk_scores : dict[str, float]
        Dictionary mapping series_id to the latest risk score (0-1).
    indicators : list[RecessionIndicator]
        List of indicator definitions.

    Returns
    -------
    pd.DataFrame
        Summary table with columns: Name, Series ID, Latest Value, Risk Score, Signal.
    """
    rows = []
    for ind in indicators:
        if ind.weight == 0:
            continue
        value = latest_values.get(ind.series_id, np.nan)
        score = risk_scores.get(ind.series_id, np.nan)

        if np.isnan(score):
            signal = "N/A"
        elif score >= 0.7:
            signal = "HIGH RISK"
        elif score >= 0.4:
            signal = "ELEVATED"
        else:
            signal = "LOW RISK"

        rows.append(
            {
                "Indicator": ind.name,
                "Series ID": ind.series_id,
                "Latest Value": round(value, 2) if not np.isnan(value) else "N/A",
                "Risk Score": round(score, 2) if not np.isnan(score) else "N/A",
                "Signal": signal,
                "Weight": round(ind.weight, 2),
                "Risk Direction": ind.risk_direction,
            }
        )

    return pd.DataFrame(rows)
