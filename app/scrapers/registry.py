"""Source registry for all available scrapers."""

from typing import Dict, List

from app.scrapers.base_scraper import BaseScraper
from app.scrapers.wf_annual_reports import WFAnnualReportsScraper
from app.scrapers.wf_earnings import WFEarningsScraper


def _build_registry() -> Dict[str, BaseScraper]:
    """Build the scraper registry with all available scrapers."""
    scrapers = [
        WFEarningsScraper(),
        WFAnnualReportsScraper(),
    ]
    return {s.name: s for s in scrapers}


SCRAPER_REGISTRY: Dict[str, BaseScraper] = _build_registry()


def get_all_sources() -> List[dict]:
    """Return metadata for all registered sources.

    Returns:
        List of dicts with name, display_name, base_url, doc_type.
    """
    return [
        {
            "name": scraper.name,
            "display_name": scraper.display_name,
            "base_url": scraper.base_url,
            "doc_type": scraper.doc_type,
        }
        for scraper in SCRAPER_REGISTRY.values()
    ]


def get_scraper(name: str) -> BaseScraper:
    """Get a scraper instance by name.

    Args:
        name: The scraper's registered name.

    Raises:
        KeyError: If no scraper with the given name exists.
    """
    if name not in SCRAPER_REGISTRY:
        raise KeyError(f"Unknown source: {name!r}. Available: {list(SCRAPER_REGISTRY.keys())}")
    return SCRAPER_REGISTRY[name]
