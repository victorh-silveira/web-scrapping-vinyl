"""Domain Ports (interfaces) following Dependency Inversion Principle (DIP)."""

from __future__ import annotations

from typing import Protocol

from vinyl_scraper.domain.entities import AlbumSearchReport, ScrapedEdition, VinylQuery
from vinyl_scraper.domain.value_objects import ASIN, BlackFridayWindow, PriceSnapshot


class AmazonScraperPort(Protocol):
    """Port for scraping vinyl editions from Amazon BR."""

    def search_vinyl_editions(self, query: VinylQuery, max_pages: int = 2) -> list[ScrapedEdition]:
        """Search Amazon BR for all vinyl editions matching `query`."""
        ...


class PriceHistoryRepositoryPort(Protocol):
    """Port for persisting and querying local price history snapshots."""

    def save_snapshots(
        self,
        snapshots: list[PriceSnapshot],
        titles_by_asin: dict[str, tuple[str, str, str, str]],
    ) -> None:
        """Persist new price snapshots and edition metadata."""
        ...

    def get_history(self, asin: ASIN) -> list[PriceSnapshot]:
        """Retrieve all stored snapshots for an ASIN ordered by timestamp."""
        ...

    def get_editions_for_query(self, query: VinylQuery) -> list[ScrapedEdition]:
        """Retrieve latest known scraped editions for a query from local storage."""
        ...


class ExternalPriceHistoryPort(Protocol):
    """Port for optional external price trackers (e.g., Keepa API)."""

    def fetch_history(self, asin: ASIN) -> list[PriceSnapshot]:
        """Fetch historical price points from an external provider."""
        ...


class CatalogReaderPort(Protocol):
    """Port for reading the input JSON vinyl wishlist."""

    def load(self) -> tuple[BlackFridayWindow, list[VinylQuery]]:
        """Return the configured BlackFridayWindow and list of VinylQuery items."""
        ...


class ReportExporterPort(Protocol):
    """Port for exporting the analyzed report."""

    def export(self, reports: list[AlbumSearchReport], window: BlackFridayWindow) -> str:
        """Export reports and return the destination path or identifier."""
        ...
