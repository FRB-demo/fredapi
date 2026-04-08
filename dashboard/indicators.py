"""
Recession indicator definitions, series IDs, weights, and risk direction.

Each indicator is defined as a dictionary with:
- series_id: FRED series identifier
- name: Human-readable name
- weight: Relative weight in the composite score (weights are normalized to sum to 1)
- risk_direction: 'high' means high values signal recession risk,
                  'low' means low values signal recession risk
- description: Brief explanation of why this indicator matters
- frequency: Native data frequency (D=daily, W=weekly, M=monthly, Q=quarterly)
- transform: Optional transformation to apply ('none', 'pch' for percent change, 'diff')
"""

from dataclasses import dataclass, field


@dataclass
class RecessionIndicator:
    """A single recession indicator definition."""

    series_id: str
    name: str
    weight: float
    risk_direction: str  # 'high' = high values signal recession, 'low' = low values signal recession
    description: str
    frequency: str  # D, W, M, Q
    transform: str = "none"  # 'none', 'pch', 'diff'
    kwargs: dict = field(default_factory=dict)

    def signal_multiplier(self) -> int:
        """Return +1 if high values mean recession risk, -1 if low values do."""
        return 1 if self.risk_direction == "high" else -1


# Default recession indicators
DEFAULT_INDICATORS: list[RecessionIndicator] = [
    RecessionIndicator(
        series_id="T10Y2Y",
        name="Yield Curve Spread (10Y-2Y)",
        weight=0.25,
        risk_direction="low",
        description=(
            "The 10-Year minus 2-Year Treasury spread. "
            "An inverted yield curve (negative spread) is a classic recession predictor."
        ),
        frequency="D",
    ),
    RecessionIndicator(
        series_id="UNRATE",
        name="Unemployment Rate",
        weight=0.15,
        risk_direction="high",
        description=(
            "The civilian unemployment rate. "
            "Rising unemployment signals economic weakness."
        ),
        frequency="M",
    ),
    RecessionIndicator(
        series_id="A191RL1Q225SBEA",
        name="Real GDP Growth (% Change)",
        weight=0.20,
        risk_direction="low",
        description=(
            "Real GDP percent change from preceding period (annualized). "
            "Negative GDP growth signals recession."
        ),
        frequency="Q",
    ),
    RecessionIndicator(
        series_id="ICSA",
        name="Initial Jobless Claims",
        weight=0.10,
        risk_direction="high",
        description=(
            "Initial claims for unemployment insurance. "
            "Spikes in claims indicate labor market deterioration."
        ),
        frequency="W",
    ),
    RecessionIndicator(
        series_id="MANEMP",
        name="Manufacturing Employment",
        weight=0.10,
        risk_direction="low",
        description=(
            "All employees in manufacturing (thousands). "
            "Declining manufacturing employment signals recession risk."
        ),
        frequency="M",
    ),
    RecessionIndicator(
        series_id="UMCSENT",
        name="Consumer Sentiment (U. Michigan)",
        weight=0.10,
        risk_direction="low",
        description=(
            "University of Michigan Consumer Sentiment Index. "
            "Low consumer confidence is associated with economic downturns."
        ),
        frequency="M",
    ),
    RecessionIndicator(
        series_id="USREC",
        name="NBER Recession Indicator",
        weight=0.0,
        risk_direction="high",
        description=(
            "NBER-based recession indicator (1 = recession, 0 = expansion). "
            "Used for validation and recession shading, not scored."
        ),
        frequency="M",
    ),
]


def get_default_indicators() -> list[RecessionIndicator]:
    """Return a copy of the default indicator list."""
    return list(DEFAULT_INDICATORS)


def get_scored_indicators(
    indicators: list[RecessionIndicator],
) -> list[RecessionIndicator]:
    """Return only indicators that contribute to the composite score (weight > 0)."""
    return [ind for ind in indicators if ind.weight > 0]


def normalize_weights(indicators: list[RecessionIndicator]) -> dict[str, float]:
    """Normalize weights of scored indicators to sum to 1.0."""
    scored = get_scored_indicators(indicators)
    total_weight = sum(ind.weight for ind in scored)
    if total_weight == 0:
        return {}
    return {ind.series_id: ind.weight / total_weight for ind in scored}
