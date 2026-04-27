# EconSight Wiki

## Comprehensive User & Developer Guide

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
   - [Running the Application](#running-the-application)
   - [Connecting to Live FRED Data](#connecting-to-live-fred-data)
3. [User Guide](#user-guide)
   - [Dashboard Layout](#dashboard-layout)
   - [Browsing Economic Indicators](#browsing-economic-indicators)
   - [Searching for Series](#searching-for-series)
   - [Interactive Charting](#interactive-charting)
   - [Forecasting](#forecasting)
   - [Research Assistant (Chat)](#research-assistant-chat)
   - [Dataset Manager](#dataset-manager)
4. [Available Economic Indicators](#available-economic-indicators)
5. [Forecasting Methods](#forecasting-methods)
6. [Chat Commands & Queries](#chat-commands--queries)
7. [Architecture & Technical Reference](#architecture--technical-reference)
   - [System Architecture](#system-architecture)
   - [Backend (Python / FastAPI)](#backend-python--fastapi)
   - [Frontend (React / Vite)](#frontend-react--vite)
   - [API Reference](#api-reference)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

---

## Overview

**EconSight** is an interactive economic research and forecasting platform designed for economists, analysts, and researchers who work with U.S. macroeconomic data. It provides:

- **30+ pre-loaded FRED series** covering GDP, inflation, labor, housing, interest rates, financial markets, and more
- **Customizable interactive charts** with line, area, and bar visualizations, dual Y-axis support, and date range filtering
- **Time-series forecasting** using Holt-Winters, ARIMA, and Linear Trend methods with configurable confidence intervals
- **Natural language research assistant** that answers questions about economic indicators, trends, and relationships
- **Custom dataset uploads** supporting CSV and Excel files with automatic date-column detection

The platform works with or without a FRED API key. Without a key, it uses high-fidelity synthetic demo data that mirrors real economic patterns (trends, seasonality, noise). With a FRED API key, it pulls live data directly from the Federal Reserve Bank of St. Louis.

---

## Getting Started

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| **Python** | 3.10+ | Backend server |
| **Node.js** | 18+ | Frontend build tool |
| **npm** | 9+ | Comes with Node.js |
| **pip** | Latest | Python package manager |

### Installation

```bash
# Clone the repository
git clone https://github.com/FRB-demo/fredapi.git
cd fredapi

# --- Backend Setup ---
cd backend
pip install -r requirements.txt
# (Optional) Create a .env file with your FRED API key
# echo "FRED_API_KEY=your_key_here" > .env

# --- Frontend Setup ---
cd ../frontend
npm install
```

> **Windows Users**: If `pip install` fails with build errors for pandas/numpy, make sure you're using Python 3.10+ so pre-built wheels are available. The `requirements.txt` uses flexible version constraints (`>=`) to maximize compatibility.

### Running the Application

You need **two terminals** running simultaneously:

**Terminal 1 -- Backend (FastAPI)**
```bash
cd backend

# Linux / macOS
uvicorn app.main:app --port 8000

# Windows (if uvicorn is not on PATH)
python -m uvicorn app.main:app --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Terminal 2 -- Frontend (Vite/React)**
```bash
cd frontend
npm run dev
```

You should see:
```
VITE v5.x.x  ready in XXX ms
  -> Local:   http://localhost:5173/
```

**Open your browser** to **http://localhost:5173** (make sure it's `http://`, not `https://`).

### Connecting to Live FRED Data

By default, EconSight uses synthetic demo data. To connect to live FRED data:

1. Get a free API key at https://fred.stlouisfed.org/docs/api/api_key.html
2. Create a `.env` file in the `backend/` directory:
   ```
   FRED_API_KEY=your_api_key_here
   ```
3. Restart the backend server

The app automatically falls back to demo data if the API key is missing or if a FRED request fails.

---

## User Guide

### Dashboard Layout

```
+-------------------------------------------------------------------+
|  [Logo] EconSight                    [Forecast] [Datasets] [Chat] |
+----------+------------------------------------------+-------------+
|          |                                          |  Forecast   |
|  DATA    |            CHART AREA                    |  or Chat    |
| EXPLORER |   Interactive visualization of           |  Panel      |
|          |   selected economic series               |  (toggle)   |
|  Search  |                                          |             |
|  Chart   |   - Line / Area / Bar charts             |             |
|  Type    |   - Dual Y-axis for mixed units          |             |
|  Date    |   - Forecast overlay with confidence      |             |
|  Range   |   - Tooltip on hover                     |             |
|          |                                          |             |
| Category |   +------------------------------------+ |             |
|  Browser |   | Stats Bar: latest value + % change | |             |
+----------+------------------------------------------+-------------+
```

The interface has four main areas:

| Area | Description |
|---|---|
| **Header** | App title + toggle buttons for Forecast, Datasets, and Chat panels |
| **Sidebar** (left) | Search bar, chart type selector, date range filter, and the Data Explorer with categorized economic series |
| **Chart Area** (center) | The main visualization area with chart, legend, tooltips, and a stats bar showing latest values |
| **Side Panels** (right) | Forecast panel, Chat panel, or Dataset Manager (toggled from header) |

### Browsing Economic Indicators

The **Data Explorer** in the sidebar organizes 30+ economic indicators into 12 categories:

1. Click a **category name** (e.g., "National Accounts") to expand it
2. Click any **series** (e.g., "GDP - Gross Domestic Product") to add it to the chart
3. The series appears in the **Active Series** section above the Data Explorer
4. Click the **X** next to an active series to remove it

You can have **multiple series** on the chart simultaneously for comparison. When two series have different units (e.g., GDP in billions vs. Unemployment Rate in percent), the chart automatically enables **dual Y-axes**.

### Searching for Series

1. Type a query in the **Search indicators...** box at the top of the sidebar
2. Press **Enter** or click **Search FRED**
3. Results appear in place of the Data Explorer
4. Click any result to add it to your chart
5. Click **Clear** to return to the category browser

Without a FRED API key, search matches against the 30+ built-in series by ID, title, and category. With an API key, it searches the full FRED database (800,000+ series).

### Interactive Charting

**Chart Types** (selectable in the sidebar):

| Type | Best For |
|---|---|
| **Line** | Time-series trends, multi-series comparison |
| **Area** | Showing magnitude over time, fill under curve |
| **Bar** | Discrete period comparisons (quarterly GDP, etc.) |

**Chart Features**:
- **Hover tooltips**: Mouse over any point to see the exact date and value
- **Legend**: Shows all active series and forecast lines. Click to toggle visibility
- **Dual Y-axis**: Automatically activates when two series have different units (left axis for first series, right for second)
- **Date range filtering**: Use the date pickers in the sidebar to zoom into a specific time period
- **Stats bar**: Bottom of the chart shows each series' latest value and period-over-period % change

**Keyboard shortcut**: Press Enter in the search box to trigger a search.

### Forecasting

1. Click **Forecast** in the header to open the Forecast panel on the right
2. **Select a series** from the dropdown (only series currently on your chart are available)
3. **Choose a method**:
   - **Auto (Best Fit)** -- tries Holt-Winters, then ARIMA, then Linear
   - **Holt-Winters** -- best for seasonal data (monthly CPI, housing starts)
   - **ARIMA(1,1,1)** -- best for stationary/differenced series
   - **Linear Trend** -- simple extrapolation
4. **Set the forecast horizon** (1-60 periods) using the slider
5. **Set the confidence level** (80%-99%) using the slider
6. Click **Run Forecast**

The forecast appears on the chart as:
- A **dashed line** continuing from the last historical data point
- A **shaded confidence band** showing the prediction interval
- A **vertical reference line** separating historical from forecast data

You can run forecasts for multiple series simultaneously. Each forecast appears in the **Active Forecasts** section where you can remove them individually.

### Research Assistant (Chat)

1. Click **Chat** in the header to open the Research Assistant panel
2. Type a question in the text box and press Enter

The chat assistant understands natural language queries about:
- Current values: *"What is the current unemployment rate?"*
- Trends: *"What's the trend in inflation?"*
- Comparisons: *"Compare GDP and unemployment"*
- Recommendations: *"What indicators should I watch for recession?"*
- Explanations: *"What is the yield curve?"*
- Forecasting tips: *"How should I forecast CPI?"*

**Quick prompts** are shown at the start of a conversation for common queries.

When the assistant identifies relevant series, it shows **"Add to chart"** buttons that let you add them with one click.

The assistant is context-aware: if you have series loaded on your chart, it analyzes that data when answering your questions (showing latest values, trends, min/max, etc.).

### Dataset Manager

1. Click **Datasets** in the header to open the Dataset Manager modal
2. **Upload** a CSV or Excel file by:
   - Dragging and dropping onto the upload area, or
   - Clicking **Choose File** and selecting from your computer
3. After upload, the file appears in the **Uploaded Datasets** list
4. Click a dataset to configure it:
   - Select the **Date Column** (auto-detected if possible)
   - Select the **Value Column** (only numeric columns are shown)
   - Click **Add to Chart**
5. The custom series appears on your chart alongside FRED data

**Supported formats**: `.csv`, `.xlsx`, `.xls`

**Data preview**: After selecting a dataset, a preview table shows the first 10 rows and up to 5 columns.

**Deleting**: Click the trash icon next to any dataset to remove it.

---

## Available Economic Indicators

### National Accounts
| Series ID | Title | Frequency | Units |
|---|---|---|---|
| GDP | Gross Domestic Product | Quarterly | Billions of Dollars |
| GDPC1 | Real Gross Domestic Product | Quarterly | Billions of Chained 2017 Dollars |
| A191RL1Q225SBEA | Real GDP Growth Rate | Quarterly | Percent Change |

### Prices & Inflation
| Series ID | Title | Frequency | Units |
|---|---|---|---|
| CPIAUCSL | Consumer Price Index (All Urban) | Monthly | Index 1982-1984=100 |
| CPILFESL | Core CPI (Less Food & Energy) | Monthly | Index 1982-1984=100 |
| PCEPI | PCE Price Index | Monthly | Index 2017=100 |
| PCEPILFE | Core PCE Price Index | Monthly | Index 2017=100 |
| T10YIE | 10-Year Breakeven Inflation Rate | Daily | Percent |

### Labor Market
| Series ID | Title | Frequency | Units |
|---|---|---|---|
| UNRATE | Unemployment Rate | Monthly | Percent |
| PAYEMS | Total Nonfarm Payrolls | Monthly | Thousands of Persons |
| JTSJOL | Job Openings: Total Nonfarm | Monthly | Thousands |
| ICSA | Initial Jobless Claims | Weekly | Number |

### Interest Rates
| Series ID | Title | Frequency | Units |
|---|---|---|---|
| FEDFUNDS | Federal Funds Effective Rate | Monthly | Percent |
| DGS10 | 10-Year Treasury Constant Maturity Rate | Daily | Percent |
| DGS2 | 2-Year Treasury Constant Maturity Rate | Daily | Percent |
| DFII10 | 10-Year TIPS Rate | Daily | Percent |
| T10Y2Y | 10-Year Minus 2-Year Treasury Spread | Daily | Percent |

### Exchange Rates
| Series ID | Title | Frequency | Units |
|---|---|---|---|
| DEXUSEU | USD/EUR Exchange Rate | Daily | USD per EUR |

### Financial Markets
| Series ID | Title | Frequency | Units |
|---|---|---|---|
| SP500 | S&P 500 Index | Daily | Index |
| NASDAQCOM | NASDAQ Composite Index | Daily | Index |
| VIXCLS | CBOE Volatility Index (VIX) | Daily | Index |

### Money Supply
| Series ID | Title | Frequency | Units |
|---|---|---|---|
| M2SL | M2 Money Supply | Monthly | Billions of Dollars |

### Housing
| Series ID | Title | Frequency | Units |
|---|---|---|---|
| HOUST | Housing Starts | Monthly | Thousands of Units |
| PERMIT | Building Permits | Monthly | Thousands of Units |
| CSUSHPINSA | Case-Shiller Home Price Index (National) | Monthly | Index Jan 2000=100 |
| MSPUS | Median Sales Price of Houses Sold | Quarterly | Dollars |

### Consumer Spending
| Series ID | Title | Frequency | Units |
|---|---|---|---|
| RSAFS | Retail Sales: Total | Monthly | Millions of Dollars |

### Production
| Series ID | Title | Frequency | Units |
|---|---|---|---|
| INDPRO | Industrial Production Index | Monthly | Index 2017=100 |

### Surveys
| Series ID | Title | Frequency | Units |
|---|---|---|---|
| UMCSENT | Consumer Sentiment (U of Michigan) | Monthly | Index 1966:Q1=100 |

### Commodities
| Series ID | Title | Frequency | Units |
|---|---|---|---|
| DCOILWTICO | Crude Oil Price: WTI | Daily | Dollars per Barrel |

---

## Forecasting Methods

### Holt-Winters (Exponential Smoothing)

**Best for**: Series with trend and/or seasonal patterns (e.g., monthly CPI, housing starts, retail sales).

**How it works**: Fits three smoothing components -- level, trend, and seasonality -- to the historical data, then projects them forward.

| Parameter | Behavior |
|---|---|
| Seasonal periods | Auto-detected: 12 for monthly, 4 for quarterly, 52 for weekly |
| Trend | Additive |
| Seasonality | Additive (if enough data: 2x seasonal periods minimum) |
| Confidence band | Based on residual standard error, widening over forecast horizon |

### ARIMA (AutoRegressive Integrated Moving Average)

**Best for**: Stationary or unit-root series where differencing removes trends (e.g., interest rates, growth rates).

**How it works**: Fits an ARIMA(1,1,1) model that combines autoregression (past values), differencing (trend removal), and moving average (past errors).

| Parameter | Value |
|---|---|
| Order | (1, 1, 1) -- AR=1, I=1, MA=1 |
| Confidence band | Native ARIMA prediction intervals |

### Linear Trend

**Best for**: Simple trend extrapolation when other methods fail or for quick visual projections.

**How it works**: Fits a straight line (OLS regression) through the historical data and extends it forward.

| Parameter | Behavior |
|---|---|
| R-squared | Returned in the result to indicate fit quality |
| Slope | Returned for interpretation (units per period) |
| Confidence band | Based on regression prediction intervals |

### Auto Mode

When you select **Auto (Best Fit)**, the system tries methods in this order:
1. Holt-Winters
2. ARIMA
3. Linear Trend

It uses the first method that succeeds. If all fail (e.g., too few data points), it returns an error.

**Minimum data requirement**: At least 5 observations are needed to run any forecast.

---

## Chat Commands & Queries

The Research Assistant uses rule-based NLP (no external LLM APIs required) to understand your queries. Here's what it can do:

### Query Types

| Intent | Example Queries | What It Returns |
|---|---|---|
| **Current Values** | "What is the current GDP?", "Latest unemployment rate" | Latest value and date for loaded series |
| **Trends** | "What's the trend in inflation?", "Is GDP going up?" | Recent trend direction + change amount |
| **Comparisons** | "Compare CPI and PCE", "GDP vs unemployment" | Side-by-side latest values, trends, and total % change |
| **Extremes** | "What's the all-time high for S&P 500?", "Min/max of CPI" | Historical min, max, and current value |
| **Explanations** | "What is the yield curve?", "Tell me about housing indicators" | Description, category, frequency, units, and current data |
| **Recommendations** | "Recommend recession indicators", "What should I watch for inflation?" | Curated list of relevant series with descriptions |
| **Forecasting Tips** | "How should I forecast this?", "Predict future values" | Method recommendations and guidance |
| **Correlations** | "How do oil prices relate to CPI?" | Known economic relationships |

### Recognized Topics

The assistant maps natural language to FRED series using aliases:

| Say this... | Gets these series |
|---|---|
| "gdp" | GDP, GDPC1, A191RL1Q225SBEA |
| "inflation" | CPIAUCSL, CPILFESL, PCEPI, PCEPILFE, T10YIE |
| "unemployment" | UNRATE |
| "jobs" / "employment" | PAYEMS, JTSJOL, ICSA |
| "interest rate" | FEDFUNDS, DGS10, DGS2 |
| "housing" / "home price" | HOUST, PERMIT, CSUSHPINSA, MSPUS |
| "stock" / "s&p" / "nasdaq" | SP500, NASDAQCOM |
| "oil" | DCOILWTICO |
| "vix" | VIXCLS |
| "yield" / "spread" | DGS10, DGS2, T10Y2Y |
| "money supply" | M2SL |
| "consumer sentiment" | UMCSENT |

### Special Recommendations

Ask about specific themes to get curated indicator lists:

- **"recession indicators"** -- Yield spread, unemployment, jobless claims, industrial production, consumer sentiment
- **"inflation analysis"** -- Headline CPI, Core CPI, PCE, Core PCE, breakeven inflation
- **"housing market"** -- Case-Shiller, median price, housing starts, permits, 10Y Treasury

---

## Architecture & Technical Reference

### System Architecture

```
Browser (localhost:5173)
    |
    |  HTTP requests to /api/*
    |  (proxied by Vite dev server)
    v
FastAPI Backend (localhost:8000)
    |
    +-- /api/data/*       --> fred_service.py    --> FRED API / Demo Data
    +-- /api/forecast/*   --> forecast_service.py --> statsmodels
    +-- /api/chat/*       --> chat_service.py    --> Rule-based NLP
    +-- /api/datasets/*   --> dataset_service.py --> In-memory store
    +-- /api/health       --> Health check
```

### Backend (Python / FastAPI)

**Directory structure:**
```
backend/
  app/
    __init__.py
    main.py              # FastAPI app initialization, CORS, router registration
    models.py            # Pydantic request/response schemas
    routers/
      data.py            # GET /series/{id}, POST /search, GET /popular, GET /categories
      forecasting.py     # POST /forecast/
      chat.py            # POST /chat/
      datasets.py        # POST /upload, GET /, GET /{id}/series, DELETE /{id}
    services/
      fred_service.py    # FRED API client + popular series catalog
      forecast_service.py # Holt-Winters, ARIMA, Linear Trend implementations
      chat_service.py    # Intent detection + response generation
      dataset_service.py # CSV/Excel parsing + in-memory storage
      demo_data.py       # Synthetic data generator (30+ series, deterministic)
  requirements.txt       # Python dependencies
  .env                   # (optional) FRED_API_KEY
```

**Key design decisions:**
- **Demo data is deterministic**: Uses `random.seed(42)` at module load + module-level cache so repeated calls return identical data
- **NaN safety**: Dataset uploads filter out NaN values before serialization to prevent JSON errors
- **None guards**: Chat service checks for `None` values before formatting to prevent `TypeError` crashes
- **Graceful degradation**: If the FRED API fails or no key is provided, all endpoints fall back to demo data automatically

### Frontend (React / Vite)

**Directory structure:**
```
frontend/
  src/
    App.jsx              # Root component, state management, layout
    main.jsx             # React DOM entry point
    index.css            # TailwindCSS base + custom styles
    components/
      Header.jsx         # Top bar with Forecast/Datasets/Chat toggles
      Sidebar.jsx        # Search, chart type, date range, Data Explorer
      ChartPanel.jsx     # Recharts visualization + stats bar
      ForecastPanel.jsx  # Forecast configuration + run
      ChatPanel.jsx      # Research Assistant chat interface
      DatasetManager.jsx # CSV/Excel upload modal
    services/
      api.js             # API client (fetch wrappers for all endpoints)
  package.json           # Node.js dependencies
  vite.config.js         # Vite config with API proxy to backend
  tailwind.config.js     # TailwindCSS configuration
  postcss.config.js      # PostCSS plugins
```

**Key libraries:**
| Library | Purpose |
|---|---|
| React 18 | UI framework |
| Recharts | Charting (ComposedChart, Line, Area, Bar, Tooltip, Legend) |
| TailwindCSS | Utility-first CSS styling |
| Lucide React | Icon library |
| React Markdown | Rendering chat responses with formatting |
| Vite | Build tool and dev server with HMR |

**State management**: All app state is managed via React `useState` hooks in `App.jsx` and passed down as props. No external state library is needed given the app's scope.

### API Reference

#### Data Endpoints

| Method | Endpoint | Description | Parameters |
|---|---|---|---|
| GET | `/api/data/series/{series_id}` | Fetch a single time series | `start_date`, `end_date` (query params, optional) |
| POST | `/api/data/multi-series` | Fetch multiple series | Body: `{ series: [{ series_id, start_date?, end_date? }] }` |
| POST | `/api/data/search` | Search for series | Body: `{ query, source?, limit? }` |
| GET | `/api/data/popular` | Get all 30+ curated series | -- |
| GET | `/api/data/categories` | Get unique category names | -- |

**Response format** (single series):
```json
{
  "series_id": "GDP",
  "title": "Gross Domestic Product",
  "units": "Billions of Dollars",
  "frequency": "Quarterly",
  "source": "FRED",
  "dates": ["2015-01-01", "2015-04-01", ...],
  "values": [18064.7, 18287.2, ...]
}
```

#### Forecast Endpoint

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/forecast/` | Generate a time-series forecast |

**Request body:**
```json
{
  "series_id": "CPIAUCSL",
  "periods": 12,
  "method": "auto",
  "confidence_level": 0.95,
  "start_date": null,
  "end_date": null
}
```

**Response:**
```json
{
  "method": "Holt-Winters",
  "series_id": "CPIAUCSL",
  "title": "Consumer Price Index (All Urban)",
  "forecast_dates": ["2025-11-01", "2025-12-01", ...],
  "forecast_values": [318.5, 319.1, ...],
  "lower_bound": [316.2, 316.5, ...],
  "upper_bound": [320.8, 321.7, ...],
  "confidence_level": 0.95,
  "historical_dates": [...],
  "historical_values": [...]
}
```

#### Chat Endpoint

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat/` | Process a natural language query |

**Request body:**
```json
{
  "message": "What is the current inflation rate?",
  "context": [
    {
      "series_id": "CPIAUCSL",
      "title": "Consumer Price Index",
      "values": [310.5, 311.2, ...],
      "dates": ["2025-08-01", "2025-09-01", ...],
      "units": "Index"
    }
  ]
}
```

**Response:**
```json
{
  "response": "Here are the latest values:\n\n- **Consumer Price Index** (CPIAUCSL): **311.20** as of 2025-09-01",
  "intent": "current",
  "suggested_series": [
    { "series_id": "CPIAUCSL", "title": "Consumer Price Index (All Urban)", "source": "FRED" }
  ]
}
```

#### Dataset Endpoints

| Method | Endpoint | Description | Parameters |
|---|---|---|---|
| POST | `/api/datasets/upload` | Upload CSV/Excel file | Multipart form: `file` |
| GET | `/api/datasets/` | List all uploaded datasets | -- |
| GET | `/api/datasets/{id}/series` | Extract time series from dataset | `date_col`, `value_col` (query params) |
| DELETE | `/api/datasets/{id}` | Delete an uploaded dataset | -- |

#### Health Check

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Server health check |

**Response:** `{"status": "ok", "version": "1.0.0"}`

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FRED_API_KEY` | *(empty)* | Your FRED API key. Get one free at https://fred.stlouisfed.org/docs/api/api_key.html |

Place environment variables in `backend/.env`:
```
FRED_API_KEY=abcdef1234567890
```

### Vite Proxy Configuration

The frontend dev server proxies all `/api/*` requests to the backend. If your backend runs on a different port, edit `frontend/vite.config.js`:

```js
proxy: {
  '/api': {
    target: 'http://localhost:8000',  // Change this to your backend port
    changeOrigin: true,
  },
},
```

### Port Configuration

| Service | Default Port | How to Change |
|---|---|---|
| Backend | 8000 | `python -m uvicorn app.main:app --port <PORT>` |
| Frontend | 5173 | Edit `server.port` in `vite.config.js` or set via CLI |

---

## Troubleshooting

### Common Issues

| Problem | Cause | Solution |
|---|---|---|
| Sidebar categories don't load | Backend not running | Start the backend on port 8000 (or whichever port your vite proxy targets) |
| "Not Found" errors in browser console | API proxy misconfigured or backend down | Verify backend is running; check `vite.config.js` proxy target matches backend port |
| `pip install` fails on Windows with meson/build errors | Python version too old or no pre-built wheels | Use Python 3.10+; the flexible version constraints in `requirements.txt` should resolve this |
| `uvicorn` not recognized (Windows) | Not on PATH | Use `python -m uvicorn app.main:app --port 8000` instead |
| SSL error when opening `localhost:5173` | Browser forcing HTTPS | Use `http://localhost:5173` (not https). Try incognito mode or a different browser |
| Port already in use | Another process on the port | Kill the process: `netstat -ano \| findstr :8000` then `taskkill /PID <PID> /F` (Windows) or `lsof -i :8000` then `kill <PID>` (macOS/Linux) |
| Forecast fails: "Need at least 5 data points" | Filtered date range has too few points | Widen your date range or select a series with more data |
| Chart shows no forecast line | Forecast on wrong Y-axis (fixed in latest) | Pull the latest code; dual-axis forecast rendering has been fixed |
| NaN error on dataset upload | Missing values in CSV | Fixed in latest code; NaN values are automatically filtered out |

### Checking Backend Health

Open http://localhost:8000/docs in your browser to see the Swagger/OpenAPI documentation. If this loads, the backend is running correctly.

Alternatively, check the health endpoint:
```bash
curl http://localhost:8000/api/health
# Expected: {"status":"ok","version":"1.0.0"}
```

### Checking Frontend Build

```bash
cd frontend
npm run build
```

This creates a production build in `frontend/dist/`. If the build succeeds, the frontend code is valid.

---

## FAQ

**Q: Do I need a FRED API key?**
A: No. The app works out of the box with synthetic demo data that closely mimics real economic patterns. A FRED API key is only needed if you want live data from the Federal Reserve.

**Q: What file formats can I upload?**
A: CSV (`.csv`), Excel (`.xlsx`), and legacy Excel (`.xls`). The system auto-detects date columns and shows only numeric columns for charting.

**Q: How many series can I chart at once?**
A: There's no hard limit, but the UI is optimized for 1-5 series. When exactly 2 series with different units are charted, dual Y-axes activate automatically.

**Q: Does the chat use an LLM / external AI?**
A: No. The Research Assistant uses rule-based NLP that runs entirely locally. No data is sent to external AI services. This means it works offline and has zero API costs, but its understanding is limited to the built-in query patterns.

**Q: Is my uploaded data stored permanently?**
A: No. Uploaded datasets are stored in server memory and are lost when the backend restarts. For persistent storage, you would need to add a database backend.

**Q: Can I use this with other data sources (BLS, BEA, Zillow, Redfin)?**
A: Yes, via the Dataset Manager. Download data from BLS, BEA, Zillow, Redfin, or any other source as CSV/Excel, then upload it to EconSight. The charting and forecasting features work identically on custom datasets.

**Q: What Python version is required?**
A: Python 3.10 or higher. This is needed for type hint syntax (`dict[str, dict]`) and for pre-built wheels of scientific packages on Windows.

**Q: Can I deploy this to production?**
A: The current setup is designed for local development. For production deployment, you would want to:
- Add a database for persistent dataset storage
- Configure proper CORS origins (currently allows all)
- Use a production ASGI server (e.g., gunicorn with uvicorn workers)
- Build the frontend (`npm run build`) and serve static files
- Add authentication/authorization as needed
