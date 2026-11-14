"""Application layer Data Transfer Objects."""

from __future__ import annotations

from dataclasses import dataclass

from vinyl_scraper.domain.entities import AlbumSearchReport
from vinyl_scraper.domain.value_objects import BlackFridayWindow


@dataclass(frozen=True)
class RunAnalysisResult:
    """Result returned by ScrapeAndAnalyzeVinylsUseCase."""

    window: BlackFridayWindow
    reports: list[AlbumSearchReport]
    output_path: str
