"""Objetos de transferência de dados (DTOs) da camada de aplicação."""

from __future__ import annotations

from dataclasses import dataclass

from vinyl_scraper.domain.entities import AlbumSearchReport
from vinyl_scraper.domain.value_objects import BlackFridayWindow


@dataclass(frozen=True)
class RunAnalysisResult:
    """Resultado retornado por ScrapeAndAnalyzeVinylsUseCase."""

    window: BlackFridayWindow
    reports: list[AlbumSearchReport]
    output_path: str
