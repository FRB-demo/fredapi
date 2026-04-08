"""
Recession Probability Dashboard — Streamlit Application.

A dashboard that uses the fredapi library to pull classic recession indicators
from FRED and compute a composite recession probability score.

Usage:
    FRED_API_KEY=your_key streamlit run dashboard/app.py
"""

import sys
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Ensure the repo root is on sys.path so we can import fredapi and dashboard modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fredapi import Fred  # noqa: E402

from dashboard.indicators import (  # noqa: E402
    RecessionIndicator,
    get_default_indicators,
    get_scored_indicators,
)
from dashboard.scoring import (  # noqa: E402
    build_indicator_summary,
    compute_composite_probability,
    compute_risk_score,
    normalize_percentile,
    normalize_zscore,
    resample_to_monthly,
)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Recession Probability Dashboard",
    page_icon="📉",
    layout="wide",
)

st.title("📉 Recession Probability Dashboard")
st.markdown(
    "Real-time recession probability computed from classic economic indicators "
    "via the [FRED API](https://fred.stlouisfed.org/)."
)

# ---------------------------------------------------------------------------
# Sidebar — API key & settings
# ---------------------------------------------------------------------------

st.sidebar.header("Settings")

api_key = st.sidebar.text_input(
    "FRED API Key",
    value=os.environ.get("FRED_API_KEY", ""),
    type="password",
    help="Get a free API key at https://fred.stlouisfed.org/docs/api/api_key.html",
)

if not api_key:
    st.warning(
        "Please enter your FRED API key in the sidebar or set the "
        "`FRED_API_KEY` environment variable."
    )
    st.stop()

# Date range
col1, col2 = st.sidebar.columns(2)
default_start = pd.Timestamp("2000-01-01")
default_end = pd.Timestamp.today()
observation_start = col1.date_input("Start Date", value=default_start)
observation_end = col2.date_input("End Date", value=default_end)

# Normalization method
norm_method = st.sidebar.selectbox(
    "Normalization Method",
    ["Percentile (expanding)", "Z-Score (expanding)"],
    index=0,
    help="How each indicator is normalized to a 0-1 risk scale.",
)

# Aggregation method
agg_method = st.sidebar.selectbox(
    "Composite Score Method",
    ["weighted_average", "geometric_mean"],
    index=0,
)

# Additional FRED kwargs
st.sidebar.subheader("Advanced FRED Parameters")
extra_units = st.sidebar.text_input(
    "Units transformation",
    value="",
    help="e.g. 'pch' for percent change — applied to all series fetches if set.",
)

# ---------------------------------------------------------------------------
# Indicator weight configuration
# ---------------------------------------------------------------------------

st.sidebar.subheader("Indicator Weights")
indicators = get_default_indicators()

for ind in indicators:
    if ind.weight > 0:
        ind.weight = st.sidebar.slider(
            ind.name,
            min_value=0.0,
            max_value=1.0,
            value=ind.weight,
            step=0.05,
            key=f"weight_{ind.series_id}",
        )

# ---------------------------------------------------------------------------
# Search for additional series
# ---------------------------------------------------------------------------

st.sidebar.subheader("Add Custom Indicator")
search_query = st.sidebar.text_input(
    "Search FRED series",
    value="",
    help="Use Fred.search() to find additional series to include.",
)

if search_query:
    try:
        fred = Fred(api_key=api_key)
        search_results = fred.search(search_query, limit=10, order_by="popularity", sort_order="desc")
        if search_results is not None and not search_results.empty:
            st.sidebar.dataframe(
                search_results[["title", "frequency", "units", "popularity"]],
                use_container_width=True,
            )
            selected_id = st.sidebar.text_input(
                "Enter Series ID to add",
                value="",
                key="custom_series_id",
            )
            custom_direction = st.sidebar.selectbox(
                "Risk direction for custom series",
                ["high", "low"],
                key="custom_direction",
            )
            custom_weight = st.sidebar.slider(
                "Weight for custom series",
                0.0, 1.0, 0.10, 0.05,
                key="custom_weight",
            )
            if selected_id:
                indicators.append(
                    RecessionIndicator(
                        series_id=selected_id.strip().upper(),
                        name=selected_id.strip().upper(),
                        weight=custom_weight,
                        risk_direction=custom_direction,
                        description="User-added custom indicator",
                        frequency="M",
                    )
                )
        else:
            st.sidebar.info("No results found.")
    except Exception as e:
        st.sidebar.error(f"Search error: {e}")


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner="Fetching data from FRED...")
def fetch_series(
    _api_key: str,
    series_id: str,
    obs_start: str,
    obs_end: str,
    extra_kwargs: dict,
) -> pd.Series:
    """Fetch a single FRED series and return as pd.Series."""
    fred = Fred(api_key=_api_key)
    kwargs = dict(extra_kwargs)
    data = fred.get_series(
        series_id,
        observation_start=obs_start,
        observation_end=obs_end,
        **kwargs,
    )
    return data


@st.cache_data(ttl=3600, show_spinner="Fetching NBER recession dates...")
def fetch_recession_dates(_api_key: str, obs_start: str, obs_end: str) -> pd.Series:
    """Fetch the USREC series for recession shading."""
    fred = Fred(api_key=_api_key)
    return fred.get_series("USREC", observation_start=obs_start, observation_end=obs_end)


# Build extra kwargs
extra_kwargs: dict[str, str] = {}
if extra_units:
    extra_kwargs["units"] = extra_units

# Fetch all series
raw_data: dict[str, pd.Series] = {}
fetch_errors: dict[str, str] = {}

progress_bar = st.progress(0, text="Fetching indicator data...")
scored_indicators = get_scored_indicators(indicators)
total = len(scored_indicators)

for i, ind in enumerate(scored_indicators):
    try:
        series = fetch_series(
            api_key,
            ind.series_id,
            str(observation_start),
            str(observation_end),
            extra_kwargs,
        )
        raw_data[ind.series_id] = series
    except Exception as e:
        fetch_errors[ind.series_id] = str(e)
    progress_bar.progress((i + 1) / total, text=f"Fetched {ind.name}")

# Fetch recession dates for shading
try:
    usrec = fetch_recession_dates(api_key, str(observation_start), str(observation_end))
    usrec = resample_to_monthly(usrec)
except Exception:
    usrec = pd.Series(dtype=float)

progress_bar.empty()

if fetch_errors:
    with st.expander("⚠️ Data fetch warnings", expanded=False):
        for sid, err in fetch_errors.items():
            st.warning(f"**{sid}**: {err}")

if not raw_data:
    st.error("No indicator data could be fetched. Check your API key and network.")
    st.stop()

# ---------------------------------------------------------------------------
# Processing — resample, normalize, score
# ---------------------------------------------------------------------------

monthly_data: dict[str, pd.Series] = {}
risk_scores: dict[str, pd.Series] = {}

for ind in scored_indicators:
    if ind.series_id not in raw_data:
        continue

    series = raw_data[ind.series_id].dropna()
    monthly = resample_to_monthly(series)

    # Normalize
    if "Percentile" in norm_method:
        normalized = normalize_percentile(monthly)
    else:
        normalized = normalize_zscore(monthly)

    # Compute risk score (flip if needed based on risk_direction)
    risk = compute_risk_score(normalized, ind)

    monthly_data[ind.series_id] = monthly
    risk_scores[ind.series_id] = risk

# Composite probability
composite = compute_composite_probability(risk_scores, indicators, method=agg_method)

# ---------------------------------------------------------------------------
# Layout — Main dashboard
# ---------------------------------------------------------------------------

# Current composite score
if not composite.empty and not composite.dropna().empty:
    current_prob = composite.dropna().iloc[-1]
    current_date = composite.dropna().index[-1]

    # Gauge header
    gauge_col, info_col = st.columns([1, 2])

    with gauge_col:
        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=current_prob * 100,
                number={"suffix": "%", "font": {"size": 48}},
                title={"text": f"Recession Probability<br><sub>{current_date:%B %Y}</sub>"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "darkred"},
                    "steps": [
                        {"range": [0, 30], "color": "#2ecc71"},
                        {"range": [30, 60], "color": "#f39c12"},
                        {"range": [60, 100], "color": "#e74c3c"},
                    ],
                    "threshold": {
                        "line": {"color": "black", "width": 4},
                        "thickness": 0.8,
                        "value": current_prob * 100,
                    },
                },
            )
        )
        fig_gauge.update_layout(height=300, margin=dict(t=80, b=20, l=40, r=40))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with info_col:
        st.subheader("Indicator Summary")
        # Build summary table
        latest_values = {
            sid: s.dropna().iloc[-1] if not s.dropna().empty else np.nan
            for sid, s in monthly_data.items()
        }
        latest_risks = {
            sid: s.dropna().iloc[-1] if not s.dropna().empty else np.nan
            for sid, s in risk_scores.items()
        }
        summary_df = build_indicator_summary(latest_values, latest_risks, indicators)
        if not summary_df.empty:
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
else:
    st.warning("Insufficient data to compute composite recession probability.")

# ---------------------------------------------------------------------------
# Helper — recession shading
# ---------------------------------------------------------------------------


def _get_recession_periods(usrec_series: pd.Series) -> list[tuple]:
    """Identify contiguous recession blocks from USREC series."""
    if usrec_series.empty:
        return []
    rec_periods = usrec_series[usrec_series == 1]
    if rec_periods.empty:
        return []
    rec_diff = rec_periods.index.to_series().diff().dt.days
    starts = [rec_periods.index[0]]
    ends: list = []
    for j in range(1, len(rec_periods)):
        if rec_diff.iloc[j] > 45:  # gap > 45 days = new recession
            ends.append(rec_periods.index[j - 1])
            starts.append(rec_periods.index[j])
    ends.append(rec_periods.index[-1])
    return list(zip(starts, ends))


def _add_recession_shading(
    fig: go.Figure,
    usrec_series: pd.Series,
    annotate_first: bool = False,
) -> None:
    """Add NBER recession shading rectangles to a plotly figure."""
    periods = _get_recession_periods(usrec_series)
    for i, (s, e) in enumerate(periods):
        fig.add_vrect(
            x0=s,
            x1=e,
            fillcolor="rgba(200,200,200,0.3)",
            layer="below",
            line_width=0,
            annotation_text="Recession" if (annotate_first and i == 0) else None,
            annotation_position="top left",
        )


# ---------------------------------------------------------------------------
# Composite probability time series
# ---------------------------------------------------------------------------

st.subheader("Composite Recession Probability Over Time")

if not composite.empty:
    fig_composite = go.Figure()

    # Recession shading
    _add_recession_shading(fig_composite, usrec, annotate_first=True)

    fig_composite.add_trace(
        go.Scatter(
            x=composite.index,
            y=composite.values * 100,
            mode="lines",
            name="Recession Probability",
            line=dict(color="#e74c3c", width=2),
            fill="tozeroy",
            fillcolor="rgba(231,76,60,0.15)",
        )
    )

    # Threshold lines
    fig_composite.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Low Risk (30%)")
    fig_composite.add_hline(y=60, line_dash="dash", line_color="orange", annotation_text="Elevated (60%)")

    fig_composite.update_layout(
        yaxis_title="Probability (%)",
        xaxis_title="Date",
        yaxis=dict(range=[0, 100]),
        height=400,
        margin=dict(t=20, b=40),
        showlegend=False,
    )
    st.plotly_chart(fig_composite, use_container_width=True)

# ---------------------------------------------------------------------------
# Individual indicator charts
# ---------------------------------------------------------------------------

st.subheader("Individual Indicators")

# Create a 2-column grid of charts
scored = get_scored_indicators(indicators)
cols_per_row = 2

for row_start in range(0, len(scored), cols_per_row):
    cols = st.columns(cols_per_row)
    for col_idx in range(cols_per_row):
        ind_idx = row_start + col_idx
        if ind_idx >= len(scored):
            break
        ind = scored[ind_idx]

        with cols[col_idx]:
            if ind.series_id not in monthly_data:
                st.caption(f"**{ind.name}** — No data available")
                continue

            series = monthly_data[ind.series_id]
            fig = go.Figure()

            # Recession shading
            _add_recession_shading(fig, usrec)

            fig.add_trace(
                go.Scatter(
                    x=series.index,
                    y=series.values,
                    mode="lines",
                    name=ind.name,
                    line=dict(width=1.5),
                )
            )

            fig.update_layout(
                title=dict(text=ind.name, font=dict(size=14)),
                height=280,
                margin=dict(t=40, b=30, l=40, r=20),
                showlegend=False,
                xaxis_title="",
                yaxis_title="",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Show risk score below chart
            if ind.series_id in risk_scores:
                risk_series = risk_scores[ind.series_id].dropna()
                if not risk_series.empty:
                    latest_risk = risk_series.iloc[-1]
                    color = (
                        "🟢" if latest_risk < 0.4
                        else "🟡" if latest_risk < 0.7
                        else "🔴"
                    )
                    st.caption(
                        f"{color} Risk Score: **{latest_risk:.1%}** | "
                        f"Direction: {ind.risk_direction} | "
                        f"Weight: {ind.weight:.0%}"
                    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #888; font-size: 0.85em;">
    Data sourced from <a href="https://fred.stlouisfed.org/">FRED</a> via
    <code>fredapi</code>. NBER recession dates used for shading.
    This dashboard is for educational/research purposes only and does not
    constitute financial advice.
    </div>
    """,
    unsafe_allow_html=True,
)
