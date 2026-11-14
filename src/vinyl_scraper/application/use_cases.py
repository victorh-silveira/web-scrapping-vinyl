"""Casos de uso da aplicação que orquestram serviços de domínio e portas."""

from __future__ import annotations

from collections.abc import Callable

from vinyl_scraper.application.dto import RunAnalysisResult
from vinyl_scraper.domain.entities import (
    AlbumSearchReport,
    ScrapedEdition,
    VinylEdition,
    VinylQuery,
)
from vinyl_scraper.domain.exceptions import ScraperBlockedError
from vinyl_scraper.domain.ports import (
    AmazonScraperPort,
    CatalogReaderPort,
    ExternalPriceHistoryPort,
    PriceHistoryRepositoryPort,
    ReportExporterPort,
)
from vinyl_scraper.domain.services import EditionClassifier, PriceAnalyticsService
from vinyl_scraper.domain.value_objects import BlackFridayWindow, PriceSnapshot


class ScrapeAndAnalyzeVinylsUseCase:
    """Orquestra coleta de vinis, enriquecimento histórico, análises e exportação de relatório."""

    def __init__(
        self,
        catalog_reader: CatalogReaderPort,
        scraper: AmazonScraperPort,
        history_repo: PriceHistoryRepositoryPort,
        external_history: ExternalPriceHistoryPort,
        exporter: ReportExporterPort,
        classifier: EditionClassifier | None = None,
        analytics: PriceAnalyticsService | None = None,
    ) -> None:
        self._catalog_reader = catalog_reader
        self._scraper = scraper
        self._history_repo = history_repo
        self._external_history = external_history
        self._exporter = exporter
        self._classifier = classifier or EditionClassifier()
        self._analytics = analytics or PriceAnalyticsService()

    def execute(
        self,
        max_pages: int = 2,
        scrape: bool = True,
        on_progress: Callable[[int, int, VinylQuery, AlbumSearchReport | None], None] | None = None,
    ) -> RunAnalysisResult:
        """Executa o pipeline completo (ou análise offline quando `scrape=False`)."""
        window, queries = self._catalog_reader.load()
        reports: list[AlbumSearchReport] = []
        total = len(queries)

        for idx, query in enumerate(queries, start=1):
            if on_progress is not None:
                on_progress(idx, total, query, None)
            report = self._process_query(
                query=query, window=window, max_pages=max_pages, scrape=scrape
            )
            reports.append(report)
            if on_progress is not None:
                on_progress(idx, total, query, report)

        output_path = self._exporter.export(reports=reports, window=window)
        return RunAnalysisResult(window=window, reports=reports, output_path=output_path)

    def _process_query(
        self,
        query: VinylQuery,
        window: BlackFridayWindow,
        max_pages: int,
        scrape: bool,
    ) -> AlbumSearchReport:
        try:
            raw_editions = (
                self._scraper.search_vinyl_editions(query, max_pages=max_pages)
                if scrape
                else self._history_repo.get_editions_for_query(query)
            )
        except ScraperBlockedError as exc:
            return AlbumSearchReport(query=query, editions=[], blocked=True, error_message=str(exc))

        # Deduplicate by ASIN keeping the lowest observed price in this run
        deduped: dict[str, ScrapedEdition] = {}
        for item in raw_editions:
            key = item.asin.value
            if key not in deduped or item.current_price < deduped[key].current_price:
                deduped[key] = item

        valid_items: list[tuple[ScrapedEdition, str]] = []
        classified_map = {}
        for item in deduped.values():
            ed_info = self._classifier.classify(item.title, query, format_hint=item.format_hint)
            if ed_info.is_vinyl:
                valid_items.append((item, ed_info.edition_label))
                classified_map[item.asin.value] = ed_info

        if scrape and valid_items:
            snapshots_to_save = [
                PriceSnapshot(
                    asin=item.asin,
                    price=item.current_price,
                    list_price=item.list_price,
                    captured_at=item.captured_at,
                    source="amazon_br",
                    seller=item.seller,
                    is_prime=item.is_prime,
                )
                for item, _ in valid_items
            ]
            meta = {
                item.asin.value: (item.title, query.artist, query.album, label)
                for item, label in valid_items
            }
            self._history_repo.save_snapshots(snapshots_to_save, meta)

        analyzed_editions: list[VinylEdition] = []
        for item, _ in valid_items:
            ed_info = classified_map[item.asin.value]
            local_history = self._history_repo.get_history(item.asin)
            ext_history = self._external_history.fetch_history(item.asin)
            merged_history = self._merge_snapshots(local_history, ext_history, item)

            stats = self._analytics.compute_stats(merged_history)
            bf_cmp = self._analytics.compare_black_friday(
                snapshots=merged_history,
                current_price=item.current_price,
                list_price=item.list_price,
                stats=stats,
                window=window,
            )
            cb_score = self._analytics.compute_cost_benefit(
                query=query,
                current_price=item.current_price,
                stats=stats,
                bf_comparison=bf_cmp,
                edition_info=ed_info,
                is_prime=item.is_prime,
                rating=item.rating,
                review_count=item.review_count,
            )
            analyzed_editions.append(
                VinylEdition(
                    asin=item.asin,
                    title=item.title,
                    url=item.url,
                    edition_info=ed_info,
                    current_price=item.current_price,
                    list_price=item.list_price,
                    is_prime=item.is_prime,
                    rating=item.rating,
                    review_count=item.review_count,
                    seller=item.seller,
                    stats=stats,
                    bf_comparison=bf_cmp,
                    cost_benefit=cb_score,
                )
            )

        analyzed_editions.sort(key=lambda e: e.cost_benefit.total_score, reverse=True)
        return AlbumSearchReport(query=query, editions=analyzed_editions)

    def _merge_snapshots(
        self,
        local_history: list[PriceSnapshot],
        ext_history: list[PriceSnapshot],
        current_item: ScrapedEdition,
    ) -> list[PriceSnapshot]:
        seen: dict[tuple[str, str], PriceSnapshot] = {}
        for snap in [*local_history, *ext_history]:
            seen[(snap.captured_at.isoformat(), snap.source)] = snap

        if not seen:
            current_snap = PriceSnapshot(
                asin=current_item.asin,
                price=current_item.current_price,
                list_price=current_item.list_price,
                captured_at=current_item.captured_at,
                source="amazon_br",
                seller=current_item.seller,
                is_prime=current_item.is_prime,
            )
            return [current_snap]

        return sorted(seen.values(), key=lambda s: s.captured_at)
