"""Default NullObject adapter for ExternalPriceHistoryPort."""

from __future__ import annotations

from vinyl_scraper.domain.value_objects import ASIN, PriceSnapshot


class NullExternalPriceHistory:
    """Default no-op external price history adapter (ready to swap for Keepa API)."""

    def fetch_history(self, asin: ASIN) -> list[PriceSnapshot]:
        """Return an empty list when no external tracker is configured."""
        return []
