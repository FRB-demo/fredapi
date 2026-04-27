"""Chat service for natural language queries about economic data.

This service provides rule-based NLP analysis without requiring any external
LLM API keys. It parses user queries and returns relevant economic insights
using the loaded data context.
"""

import re
import statistics
from datetime import datetime
from typing import Optional

from app.services.fred_service import POPULAR_SERIES, get_popular_series


# Known economic indicators and their common names
INDICATOR_ALIASES = {
    "gdp": ["GDP", "GDPC1", "A191RL1Q225SBEA"],
    "inflation": ["CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE", "T10YIE"],
    "cpi": ["CPIAUCSL", "CPILFESL"],
    "pce": ["PCEPI", "PCEPILFE"],
    "unemployment": ["UNRATE"],
    "jobs": ["PAYEMS", "JTSJOL", "ICSA"],
    "employment": ["PAYEMS", "JTSJOL", "ICSA"],
    "nonfarm": ["PAYEMS"],
    "payrolls": ["PAYEMS"],
    "interest rate": ["FEDFUNDS", "DGS10", "DGS2"],
    "fed funds": ["FEDFUNDS"],
    "treasury": ["DGS10", "DGS2", "DFII10"],
    "yield": ["DGS10", "DGS2", "T10Y2Y"],
    "housing": ["HOUST", "PERMIT", "CSUSHPINSA", "MSPUS"],
    "home price": ["CSUSHPINSA", "MSPUS"],
    "housing starts": ["HOUST"],
    "retail": ["RSAFS"],
    "industrial": ["INDPRO"],
    "consumer sentiment": ["UMCSENT"],
    "oil": ["DCOILWTICO"],
    "vix": ["VIXCLS"],
    "stock": ["SP500", "NASDAQCOM"],
    "s&p": ["SP500"],
    "nasdaq": ["NASDAQCOM"],
    "money supply": ["M2SL"],
    "exchange rate": ["DEXUSEU"],
    "breakeven": ["T10YIE"],
    "tips": ["DFII10"],
    "spread": ["T10Y2Y"],
    "claims": ["ICSA"],
    "job openings": ["JTSJOL"],
}


def _identify_series_from_query(query: str) -> list[str]:
    """Identify which FRED series IDs are relevant to the query."""
    query_lower = query.lower()
    matched = set()

    for alias, series_ids in INDICATOR_ALIASES.items():
        if alias in query_lower:
            matched.update(series_ids)

    # Also check direct series ID mentions
    for sid in POPULAR_SERIES:
        if sid.lower() in query_lower or sid in query:
            matched.add(sid)

    return list(matched)


def _analyze_data_context(context: list[dict]) -> dict:
    """Analyze provided data context and return statistical summary."""
    summaries = {}
    for ctx in context:
        sid = ctx.get("series_id", "Unknown")
        values = ctx.get("values", [])
        dates = ctx.get("dates", [])
        title = ctx.get("title", sid)

        if not values:
            continue

        recent_values = values[-12:] if len(values) >= 12 else values
        all_values = [v for v in values if v is not None]

        summary = {
            "title": title,
            "series_id": sid,
            "total_observations": len(values),
            "latest_value": values[-1] if values else None,
            "latest_date": dates[-1] if dates else None,
        }

        if len(all_values) >= 2:
            summary["mean"] = round(statistics.mean(all_values), 2)
            summary["std_dev"] = round(statistics.stdev(all_values), 2)
            summary["min"] = round(min(all_values), 2)
            summary["max"] = round(max(all_values), 2)
            summary["change_from_start"] = round(all_values[-1] - all_values[0], 2)
            summary["pct_change_total"] = round(
                ((all_values[-1] - all_values[0]) / abs(all_values[0])) * 100, 2
            ) if all_values[0] != 0 else None

        if len(recent_values) >= 2:
            recent_change = recent_values[-1] - recent_values[0]
            summary["recent_trend"] = "increasing" if recent_change > 0 else "decreasing" if recent_change < 0 else "flat"
            summary["recent_change"] = round(recent_change, 2)

        summaries[sid] = summary

    return summaries


def _detect_query_intent(query: str) -> str:
    """Detect the intent of the user's query."""
    query_lower = query.lower()

    if any(w in query_lower for w in ["trend", "direction", "moving", "going"]):
        return "trend"
    if any(w in query_lower for w in ["compare", "comparison", "vs", "versus", "difference"]):
        return "compare"
    if any(w in query_lower for w in ["forecast", "predict", "future", "project", "outlook"]):
        return "forecast"
    if any(w in query_lower for w in ["latest", "current", "now", "today", "recent"]):
        return "current"
    if any(w in query_lower for w in ["high", "low", "max", "min", "peak", "trough"]):
        return "extremes"
    if any(w in query_lower for w in ["average", "mean", "typical"]):
        return "average"
    if any(w in query_lower for w in ["correlat", "relationship", "relate", "affect"]):
        return "correlation"
    if any(w in query_lower for w in ["what is", "what are", "explain", "tell me about", "describe"]):
        return "explain"
    if any(w in query_lower for w in ["suggest", "recommend", "which", "what should"]):
        return "recommend"
    return "general"


def _generate_trend_response(summaries: dict) -> str:
    """Generate a response about trends in the data."""
    if not summaries:
        return "I don't have data loaded to analyze trends. Try adding some series to your chart first, then ask me about trends."

    parts = []
    for sid, s in summaries.items():
        trend = s.get("recent_trend", "unknown")
        change = s.get("recent_change", 0)
        latest = s.get("latest_value")
        title = s.get("title", sid)

        part = f"**{title}** ({sid}): The recent trend is **{trend}**"
        if latest is not None:
            part += f", with the latest value at **{latest:,.2f}**"
        if change:
            part += f" (recent change: {change:+,.2f})"
        part += "."
        parts.append(part)

    return "Here's the trend analysis:\n\n" + "\n\n".join(parts)


def _generate_current_response(summaries: dict) -> str:
    """Generate a response about current values."""
    if not summaries:
        return "No data is currently loaded. Add some economic series to view current values."

    parts = []
    for sid, s in summaries.items():
        title = s.get("title", sid)
        latest = s.get("latest_value")
        date = s.get("latest_date", "")
        if latest is not None:
            parts.append(f"- **{title}** ({sid}): **{latest:,.2f}** as of {date}")
        else:
            parts.append(f"- **{title}** ({sid}): **N/A** as of {date}")

    return "Here are the latest values:\n\n" + "\n".join(parts)


def _generate_extremes_response(summaries: dict) -> str:
    """Generate a response about highs and lows."""
    if not summaries:
        return "No data loaded to analyze extremes."

    parts = []
    for sid, s in summaries.items():
        title = s.get("title", sid)
        mn = s.get("min")
        mx = s.get("max")
        latest = s.get("latest_value")
        if mn is not None and mx is not None:
            current_str = f"{latest:,.2f}" if latest is not None else "N/A"
            parts.append(
                f"- **{title}** ({sid}): Range from **{mn:,.2f}** to **{mx:,.2f}** "
                f"(current: {current_str})"
            )

    return "Extremes analysis:\n\n" + "\n".join(parts)


def _generate_explanation(query: str, summaries: dict) -> str:
    """Generate an explanation of economic indicators."""
    series_ids = _identify_series_from_query(query)

    if not series_ids and not summaries:
        # General economic explanation
        return (
            "I can help you explore a wide range of U.S. economic data. Here are some areas I cover:\n\n"
            "- **GDP & Growth**: Real GDP, GDP growth rate\n"
            "- **Inflation**: CPI, Core CPI, PCE, Core PCE, Breakeven inflation\n"
            "- **Labor Market**: Unemployment rate, Nonfarm payrolls, Job openings, Initial claims\n"
            "- **Interest Rates**: Fed Funds rate, Treasury yields (2Y, 10Y), TIPS, Yield spread\n"
            "- **Housing**: Housing starts, Building permits, Case-Shiller index, Median home price\n"
            "- **Financial Markets**: S&P 500, NASDAQ, VIX, Oil prices\n"
            "- **Other**: Retail sales, Industrial production, Consumer sentiment, Money supply\n\n"
            "Try asking about a specific indicator, e.g., 'What is the current unemployment rate?' "
            "or 'Show me inflation trends.'"
        )

    parts = []
    for sid in series_ids:
        if sid in POPULAR_SERIES:
            info = POPULAR_SERIES[sid]
            parts.append(
                f"**{info['title']}** ({sid})\n"
                f"  - Category: {info['category']}\n"
                f"  - Frequency: {info['frequency']}\n"
                f"  - Units: {info['units']}"
            )

    # Add current data if available
    if summaries:
        for sid in series_ids:
            if sid in summaries:
                s = summaries[sid]
                latest_val = s.get('latest_value')
                if latest_val is not None:
                    parts.append(
                        f"  - Latest: {latest_val:,.2f} "
                        f"(as of {s.get('latest_date', 'N/A')})"
                    )

    if parts:
        return "\n\n".join(parts)
    return "I couldn't find specific information about that. Try asking about GDP, inflation, unemployment, housing, or interest rates."


def _generate_recommendation(query: str) -> str:
    """Generate recommendations for what to explore."""
    query_lower = query.lower()

    if "recession" in query_lower:
        return (
            "To monitor recession risk, consider watching these key indicators:\n\n"
            "1. **T10Y2Y** - 10Y-2Y Treasury Spread (yield curve inversion is a classic recession signal)\n"
            "2. **UNRATE** - Unemployment Rate (rising unemployment signals weakness)\n"
            "3. **ICSA** - Initial Jobless Claims (early labor market warning)\n"
            "4. **INDPRO** - Industrial Production (decline signals manufacturing weakness)\n"
            "5. **UMCSENT** - Consumer Sentiment (falling confidence precedes slowdowns)\n\n"
            "Try adding these to your dashboard for a comprehensive recession watch."
        )

    if "inflation" in query_lower:
        return (
            "For a comprehensive inflation analysis, I recommend:\n\n"
            "1. **CPIAUCSL** - Headline CPI (broadest consumer price measure)\n"
            "2. **CPILFESL** - Core CPI (excludes volatile food & energy)\n"
            "3. **PCEPI** - PCE Price Index (the Fed's preferred measure)\n"
            "4. **PCEPILFE** - Core PCE (Fed's key target at 2%)\n"
            "5. **T10YIE** - 10-Year Breakeven Inflation (market expectations)\n\n"
            "Compare these to see the full inflation picture."
        )

    if any(w in query_lower for w in ["housing", "home", "real estate"]):
        return (
            "For housing market analysis, key series to watch:\n\n"
            "1. **CSUSHPINSA** - Case-Shiller National Home Price Index\n"
            "2. **MSPUS** - Median Sales Price of Houses\n"
            "3. **HOUST** - Housing Starts (new construction activity)\n"
            "4. **PERMIT** - Building Permits (forward-looking indicator)\n"
            "5. **DGS10** - 10-Year Treasury (influences mortgage rates)\n\n"
            "These together give a comprehensive view of housing trends."
        )

    return (
        "Here are some popular starting points for economic analysis:\n\n"
        "- **Macro Overview**: GDP, Unemployment Rate, CPI\n"
        "- **Fed Policy Watch**: Fed Funds Rate, 10Y Treasury, Yield Curve\n"
        "- **Market Pulse**: S&P 500, VIX, Oil Prices\n"
        "- **Housing Health**: Case-Shiller Index, Housing Starts\n"
        "- **Labor Deep Dive**: Payrolls, Job Openings, Claims\n\n"
        "What area would you like to explore?"
    )


def process_chat_message(message: str, context: Optional[list[dict]] = None) -> dict:
    """Process a chat message and return an intelligent response."""
    intent = _detect_query_intent(message)
    summaries = _analyze_data_context(context) if context else {}
    series_ids = _identify_series_from_query(message)

    if intent == "trend":
        response = _generate_trend_response(summaries)
    elif intent == "current":
        response = _generate_current_response(summaries)
    elif intent == "extremes":
        response = _generate_extremes_response(summaries)
    elif intent == "explain":
        response = _generate_explanation(message, summaries)
    elif intent == "recommend":
        response = _generate_recommendation(message)
    elif intent == "forecast":
        if summaries:
            response = (
                "I can see you have data loaded. To forecast, use the **Forecast** panel "
                "on the chart page. You can select your preferred method (Holt-Winters, ARIMA, "
                "or Linear Trend) and set the forecast horizon.\n\n"
                "Quick tip: Holt-Winters works best for seasonal data, ARIMA for stationary series, "
                "and Linear Trend for simple projections."
            )
        else:
            response = (
                "To generate a forecast, first add a data series to your chart, then use the "
                "**Forecast** panel. I support three methods:\n\n"
                "1. **Holt-Winters** - Best for seasonal patterns (e.g., monthly CPI)\n"
                "2. **ARIMA** - Best for stationary or differenced series\n"
                "3. **Linear Trend** - Simple extrapolation of the overall trend"
            )
    elif intent == "compare":
        if len(summaries) >= 2:
            items = list(summaries.values())
            parts = ["Here's a comparison of your loaded series:\n"]
            for s in items:
                latest_val = s.get('latest_value')
                latest_str = f"{latest_val:,.2f}" if isinstance(latest_val, (int, float)) else "N/A"
                pct = s.get('pct_change_total')
                pct_str = f"{pct:.2f}%" if pct is not None else "N/A"
                parts.append(
                    f"- **{s['title']}**: Latest = {latest_str}, "
                    f"Trend = {s.get('recent_trend', 'N/A')}, "
                    f"Total Change = {pct_str}"
                )
            response = "\n".join(parts)
        else:
            response = "Add at least two series to your chart to compare them. You can search for series in the Data Explorer panel."
    elif intent == "correlation":
        response = (
            "Correlation analysis works best when you have multiple series loaded. "
            "Add two or more series to your chart and I can describe their relationship.\n\n"
            "Some well-known economic relationships:\n"
            "- Unemployment vs. Inflation (Phillips Curve)\n"
            "- Yield Curve vs. Recession risk\n"
            "- Oil prices vs. CPI\n"
            "- Fed Funds Rate vs. Treasury yields"
        )
    else:
        # General response
        if summaries:
            response = _generate_current_response(summaries)
            response += "\n\nYou can ask me about trends, comparisons, forecasts, or specific indicators."
        elif series_ids:
            response = _generate_explanation(message, summaries)
        else:
            response = _generate_explanation(message, summaries)

    # Include suggested series if identified from query
    suggested = []
    for sid in series_ids[:5]:
        if sid in POPULAR_SERIES:
            suggested.append({
                "series_id": sid,
                "title": POPULAR_SERIES[sid]["title"],
                "source": "FRED",
            })

    return {
        "response": response,
        "intent": intent,
        "suggested_series": suggested,
    }
