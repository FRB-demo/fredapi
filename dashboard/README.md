# Recession Probability Dashboard

A Streamlit-based dashboard that uses the `fredapi` library to pull classic recession indicators from FRED and compute a composite recession probability score.

## Features

- **Composite Recession Probability**: Weighted score combining multiple economic indicators, displayed as a gauge and time series chart.
- **Individual Indicator Charts**: Each indicator plotted with NBER recession shading for historical context.
- **Indicator Summary Table**: Current values, risk scores, and signal levels for all indicators at a glance.
- **Configurable Weights**: Adjust indicator weights in real time via the sidebar.
- **Custom Indicators**: Search FRED for additional series and add them dynamically.
- **Date Range Selection**: Choose the observation window using the `observation_start` and `observation_end` parameters supported by `Fred.get_series()`.
- **Advanced FRED Parameters**: Pass additional kwargs (e.g., `units='pch'` for percent change) to all series fetches.

## Default Indicators

| Indicator | Series ID | Risk Direction | Default Weight |
|---|---|---|---|
| Yield Curve Spread (10Y-2Y) | `T10Y2Y` | Low values = risk (inverted curve) | 25% |
| Unemployment Rate | `UNRATE` | High values = risk | 15% |
| Real GDP Growth (% Change) | `A191RL1Q225SBEA` | Low values = risk | 20% |
| Initial Jobless Claims | `ICSA` | High values = risk | 10% |
| Manufacturing Employment | `MANEMP` | Low values = risk | 10% |
| Consumer Sentiment (U. Michigan) | `UMCSENT` | Low values = risk | 10% |

NBER Recession dates (`USREC`) are used for validation shading but do not contribute to the score.

## Setup

### 1. Get a FRED API Key

1. Go to [https://fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)
2. Sign up for a free account and request an API key.
3. Set the key as an environment variable:

```bash
export FRED_API_KEY=your_api_key_here
```

Alternatively, you can enter the key directly in the dashboard sidebar.

### 2. Install Dependencies

From the repository root:

```bash
pip install -e .                          # Install fredapi
pip install -r dashboard/requirements.txt  # Install dashboard dependencies
```

### 3. Run the Dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard will open in your browser at `http://localhost:8501`.

## Project Structure

```
dashboard/
├── __init__.py          # Package marker
├── app.py               # Main Streamlit application
├── indicators.py        # Indicator definitions, weights, and risk direction
├── scoring.py           # Normalization and composite probability computation
├── requirements.txt     # Dashboard-specific dependencies
└── README.md            # This file
```

## How the Scoring Works

1. **Data Fetching**: Each indicator series is pulled from FRED using `Fred.get_series()`.
2. **Resampling**: All series are resampled to monthly frequency to align different data frequencies (daily, weekly, monthly, quarterly).
3. **Normalization**: Each indicator is normalized to a 0–1 scale using either expanding historical percentile rank or expanding z-score (mapped through a sigmoid function).
4. **Risk Scoring**: For indicators where *high* values signal recession risk, the normalized score is used directly. For indicators where *low* values signal risk, the score is inverted (1 − score).
5. **Composite Score**: A weighted average (or geometric mean) of all risk scores produces the final recession probability, with weights re-normalized to account for any missing data.

## Configuration

### Via the Dashboard UI

- **Indicator weights**: Adjust sliders in the sidebar.
- **Date range**: Set start and end dates.
- **Normalization method**: Choose between percentile or z-score normalization.
- **Composite method**: Choose between weighted average or geometric mean aggregation.
- **Custom indicators**: Search FRED and add new series with custom risk direction and weight.
- **Units transformation**: Apply FRED API unit transformations (e.g., `pch` for percent change).

### Programmatic Configuration

Edit `dashboard/indicators.py` to modify the `DEFAULT_INDICATORS` list — change series IDs, weights, risk directions, or add new indicators.
