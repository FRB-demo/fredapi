"""Unified economic indicators catalog - single source of truth.

Addresses: B-7 (duplicated series catalog across fred_service, demo_data, chat_service).
All indicator metadata, demo data configs, and chat aliases are derived from this module.
"""


class Indicator:
    """An economic indicator definition."""

    __slots__ = ("series_id", "title", "category", "frequency", "units", "aliases",
                 "demo_start", "demo_end", "demo_noise", "demo_seasonal_amp", "demo_seasonal_period",
                 "demo_dates_type", "demo_value_clamp_min", "demo_value_clamp_max", "demo_round")

    def __init__(
        self,
        series_id: str,
        title: str,
        category: str,
        frequency: str,
        units: str,
        aliases: tuple[str, ...] = (),
        demo_start: float = 100.0,
        demo_end: float = 120.0,
        demo_noise: float = 0.02,
        demo_seasonal_amp: float = 0.0,
        demo_seasonal_period: int = 12,
        demo_dates_type: str = "monthly",
        demo_value_clamp_min: float | None = None,
        demo_value_clamp_max: float | None = None,
        demo_round: int = 2,
    ):
        self.series_id = series_id
        self.title = title
        self.category = category
        self.frequency = frequency
        self.units = units
        self.aliases = aliases
        self.demo_start = demo_start
        self.demo_end = demo_end
        self.demo_noise = demo_noise
        self.demo_seasonal_amp = demo_seasonal_amp
        self.demo_seasonal_period = demo_seasonal_period
        self.demo_dates_type = demo_dates_type
        self.demo_value_clamp_min = demo_value_clamp_min
        self.demo_value_clamp_max = demo_value_clamp_max
        self.demo_round = demo_round


# Master catalog of all supported economic indicators
CATALOG: list[Indicator] = [
    # National Accounts
    Indicator("GDP", "Gross Domestic Product", "National Accounts", "Quarterly", "Billions of Dollars",
             aliases=("gdp",), demo_start=18000, demo_end=29000, demo_noise=0.005, demo_dates_type="quarterly"),
    Indicator("GDPC1", "Real Gross Domestic Product", "National Accounts", "Quarterly", "Billions of Chained 2017 Dollars",
             aliases=("gdp",), demo_start=18500, demo_end=22500, demo_noise=0.005, demo_dates_type="quarterly"),
    Indicator("A191RL1Q225SBEA", "Real GDP Growth Rate", "National Accounts", "Quarterly", "Percent Change",
             aliases=("gdp",), demo_start=2.5, demo_end=2.2, demo_noise=0.5, demo_dates_type="quarterly"),

    # Prices
    Indicator("CPIAUCSL", "Consumer Price Index (All Urban)", "Prices", "Monthly", "Index 1982-1984=100",
             aliases=("inflation", "cpi"), demo_start=237, demo_end=315, demo_noise=0.002, demo_seasonal_amp=0.3),
    Indicator("CPILFESL", "Core CPI (Less Food & Energy)", "Prices", "Monthly", "Index 1982-1984=100",
             aliases=("inflation", "cpi"), demo_start=244, demo_end=320, demo_noise=0.001, demo_seasonal_amp=0.1),
    Indicator("PCEPI", "PCE Price Index", "Prices", "Monthly", "Index 2017=100",
             aliases=("inflation", "pce"), demo_start=100, demo_end=128, demo_noise=0.002, demo_seasonal_amp=0.15),
    Indicator("PCEPILFE", "Core PCE Price Index", "Prices", "Monthly", "Index 2017=100",
             aliases=("inflation", "pce"), demo_start=100, demo_end=125, demo_noise=0.001),
    Indicator("T10YIE", "10-Year Breakeven Inflation Rate", "Prices", "Daily", "Percent",
             aliases=("inflation", "breakeven"), demo_start=1.7, demo_end=2.3, demo_noise=0.03, demo_dates_type="daily",
             demo_value_clamp_min=0.5),

    # Labor Market
    Indicator("UNRATE", "Unemployment Rate", "Labor Market", "Monthly", "Percent",
             aliases=("unemployment",), demo_start=5.0, demo_end=3.8, demo_noise=0.05, demo_seasonal_amp=0.2,
             demo_value_clamp_min=3.0, demo_value_clamp_max=15.0, demo_round=1),
    Indicator("PAYEMS", "Total Nonfarm Payrolls", "Labor Market", "Monthly", "Thousands of Persons",
             aliases=("jobs", "employment", "nonfarm", "payrolls"), demo_start=143000, demo_end=157000, demo_noise=0.002, demo_seasonal_amp=100),
    Indicator("JTSJOL", "Job Openings: Total Nonfarm", "Labor Market", "Monthly", "Thousands",
             aliases=("jobs", "employment", "job openings"), demo_start=5800, demo_end=8800, demo_noise=0.03),
    Indicator("ICSA", "Initial Jobless Claims", "Labor Market", "Weekly", "Number",
             aliases=("jobs", "employment", "claims"), demo_start=220000, demo_end=210000, demo_noise=0.05),

    # Interest Rates
    Indicator("FEDFUNDS", "Federal Funds Effective Rate", "Interest Rates", "Monthly", "Percent",
             aliases=("interest rate", "fed funds"), demo_start=0.25, demo_end=5.25, demo_noise=0.03,
             demo_value_clamp_min=0.0),
    Indicator("DGS10", "10-Year Treasury Constant Maturity Rate", "Interest Rates", "Daily", "Percent",
             aliases=("interest rate", "treasury", "yield"), demo_start=1.8, demo_end=4.2, demo_noise=0.02,
             demo_dates_type="daily", demo_value_clamp_min=0.5),
    Indicator("DGS2", "2-Year Treasury Constant Maturity Rate", "Interest Rates", "Daily", "Percent",
             aliases=("interest rate", "treasury", "yield"), demo_start=1.5, demo_end=4.5, demo_noise=0.025,
             demo_dates_type="daily", demo_value_clamp_min=0.1),
    Indicator("T10Y2Y", "10-Year Minus 2-Year Treasury Spread", "Interest Rates", "Daily", "Percent",
             aliases=("yield", "spread"), demo_start=0.3, demo_end=-0.3, demo_noise=0.15, demo_dates_type="daily"),
    Indicator("DFII10", "10-Year TIPS Rate", "Interest Rates", "Daily", "Percent",
             aliases=("tips",), demo_start=-0.5, demo_end=2.0, demo_noise=0.03, demo_dates_type="daily"),

    # Exchange Rates
    Indicator("DEXUSEU", "USD/EUR Exchange Rate", "Exchange Rates", "Daily", "USD per EUR",
             aliases=("exchange rate",), demo_start=1.12, demo_end=1.08, demo_noise=0.005, demo_dates_type="daily",
             demo_round=4),

    # Financial Markets
    Indicator("VIXCLS", "CBOE Volatility Index (VIX)", "Financial Markets", "Daily", "Index",
             aliases=("vix",), demo_start=18, demo_end=16, demo_noise=0.15, demo_dates_type="daily",
             demo_value_clamp_min=10),
    Indicator("SP500", "S&P 500 Index", "Financial Markets", "Daily", "Index",
             aliases=("stock", "s&p"), demo_start=3200, demo_end=5400, demo_noise=0.008, demo_dates_type="daily"),
    Indicator("NASDAQCOM", "NASDAQ Composite Index", "Financial Markets", "Daily", "Index",
             aliases=("stock", "nasdaq"), demo_start=9000, demo_end=17000, demo_noise=0.01, demo_dates_type="daily"),

    # Money Supply
    Indicator("M2SL", "M2 Money Supply", "Money Supply", "Monthly", "Billions of Dollars",
             aliases=("money supply",), demo_start=12500, demo_end=21000, demo_noise=0.003),

    # Housing
    Indicator("HOUST", "Housing Starts", "Housing", "Monthly", "Thousands of Units",
             aliases=("housing", "housing starts"), demo_start=1100, demo_end=1400, demo_noise=0.04,
             demo_seasonal_amp=80),
    Indicator("PERMIT", "Building Permits", "Housing", "Monthly", "Thousands of Units",
             aliases=("housing",), demo_start=1200, demo_end=1500, demo_noise=0.03, demo_seasonal_amp=60),
    Indicator("CSUSHPINSA", "Case-Shiller Home Price Index (National)", "Housing", "Monthly", "Index Jan 2000=100",
             aliases=("housing", "home price"), demo_start=175, demo_end=310, demo_noise=0.003),
    Indicator("MSPUS", "Median Sales Price of Houses Sold", "Housing", "Quarterly", "Dollars",
             aliases=("housing", "home price"), demo_start=290000, demo_end=420000, demo_noise=0.01,
             demo_dates_type="quarterly"),

    # Consumer Spending
    Indicator("RSAFS", "Retail Sales: Total", "Consumer Spending", "Monthly", "Millions of Dollars",
             aliases=("retail",), demo_start=450000, demo_end=700000, demo_noise=0.01, demo_seasonal_amp=15000),

    # Production
    Indicator("INDPRO", "Industrial Production Index", "Production", "Monthly", "Index 2017=100",
             aliases=("industrial",), demo_start=103, demo_end=104, demo_noise=0.005, demo_seasonal_amp=0.5),

    # Surveys
    Indicator("UMCSENT", "Consumer Sentiment (U of Michigan)", "Surveys", "Monthly", "Index 1966:Q1=100",
             aliases=("consumer sentiment",), demo_start=92, demo_end=68, demo_noise=0.04),

    # Commodities
    Indicator("DCOILWTICO", "Crude Oil Price: WTI", "Commodities", "Daily", "Dollars per Barrel",
             aliases=("oil",), demo_start=55, demo_end=75, demo_noise=0.03, demo_dates_type="daily",
             demo_value_clamp_min=20),
]

# --- Derived lookup structures ---

# {series_id: Indicator}
CATALOG_BY_ID: dict[str, Indicator] = {ind.series_id: ind for ind in CATALOG}

# {series_id: {title, category, frequency, units}} for backward compat with POPULAR_SERIES
POPULAR_SERIES: dict[str, dict[str, str]] = {
    ind.series_id: {
        "title": ind.title,
        "category": ind.category,
        "frequency": ind.frequency,
        "units": ind.units,
    }
    for ind in CATALOG
}

# {alias: [series_ids]} for chat service
INDICATOR_ALIASES: dict[str, list[str]] = {}
for _ind in CATALOG:
    for _alias in _ind.aliases:
        if _alias not in INDICATOR_ALIASES:
            INDICATOR_ALIASES[_alias] = []
        if _ind.series_id not in INDICATOR_ALIASES[_alias]:
            INDICATOR_ALIASES[_alias].append(_ind.series_id)
