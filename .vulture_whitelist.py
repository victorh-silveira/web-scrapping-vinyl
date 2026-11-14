# Vulture whitelist for framework-invoked entrypoints and Protocol methods
from vinyl_scraper.domain.ports import (
    AmazonScraperPort,
    CatalogReaderPort,
    ExternalPriceHistoryPort,
    PriceHistoryRepositoryPort,
    ReportExporterPort,
)
from vinyl_scraper.presentation.cli import analyze_command, run_command

_ = (
    AmazonScraperPort.search_vinyl_editions,
    CatalogReaderPort.load,
    ExternalPriceHistoryPort.fetch_history,
    PriceHistoryRepositoryPort.save_snapshots,
    PriceHistoryRepositoryPort.get_history,
    PriceHistoryRepositoryPort.get_editions_for_query,
    ReportExporterPort.export,
    run_command,
    analyze_command,
)
