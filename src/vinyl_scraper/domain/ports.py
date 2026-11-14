"""Portas de domínio (interfaces) seguindo o Princípio da Inversão de Dependência (DIP)."""

from __future__ import annotations

from typing import Protocol

from vinyl_scraper.domain.entities import AlbumSearchReport, ScrapedEdition, VinylQuery
from vinyl_scraper.domain.value_objects import ASIN, BlackFridayWindow, PriceSnapshot


class AmazonScraperPort(Protocol):
    """Porta para coleta de edições de vinil na Amazon BR."""

    def search_vinyl_editions(self, query: VinylQuery, max_pages: int = 2) -> list[ScrapedEdition]:
        """Busca na Amazon BR todas as edições em vinil correspondentes a `query`."""
        ...


class PriceHistoryRepositoryPort(Protocol):
    """Porta para persistência e consulta de snapshots locais de histórico de preços."""

    def save_snapshots(
        self,
        snapshots: list[PriceSnapshot],
        titles_by_asin: dict[str, tuple[str, str, str, str]],
    ) -> None:
        """Persiste novos snapshots de preço e metadados das edições."""
        ...

    def get_history(self, asin: ASIN) -> list[PriceSnapshot]:
        """Recupera todos os snapshots armazenados de um ASIN ordenados por data."""
        ...

    def get_editions_for_query(self, query: VinylQuery) -> list[ScrapedEdition]:
        """Recupera as edições coletadas mais recentes para uma busca no armazenamento local."""
        ...


class ExternalPriceHistoryPort(Protocol):
    """Porta para rastreadores externos opcionais de preços (ex.: Keepa API)."""

    def fetch_history(self, asin: ASIN) -> list[PriceSnapshot]:
        """Busca pontos históricos de preço em um provedor externo."""
        ...


class CatalogReaderPort(Protocol):
    """Porta para leitura do catálogo JSON de discos desejados."""

    def load(self) -> tuple[BlackFridayWindow, list[VinylQuery]]:
        """Retorna o BlackFridayWindow configurado e a lista de itens VinylQuery."""
        ...


class ReportExporterPort(Protocol):
    """Porta para exportação do relatório analisado."""

    def export(self, reports: list[AlbumSearchReport], window: BlackFridayWindow) -> str:
        """Exporta os relatórios e retorna o caminho ou identificador de destino."""
        ...
