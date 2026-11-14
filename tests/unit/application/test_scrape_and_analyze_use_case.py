from datetime import UTC, datetime

from vinyl_scraper.application.use_cases import ScrapeAndAnalyzeVinylsUseCase
from vinyl_scraper.domain.entities import AlbumSearchReport, ScrapedEdition, VinylQuery
from vinyl_scraper.domain.exceptions import ScraperBlockedError
from vinyl_scraper.domain.value_objects import ASIN, BlackFridayWindow, Money, PriceSnapshot


class FakeCatalogReader:
    def __init__(self, window: BlackFridayWindow, queries: list[VinylQuery]) -> None:
        self._window = window
        self._queries = queries

    def load(self) -> tuple[BlackFridayWindow, list[VinylQuery]]:
        return self._window, self._queries


class FakeScraper:
    def __init__(self, results_by_album: dict[str, list[ScrapedEdition] | Exception]) -> None:
        self._results = results_by_album

    def search_vinyl_editions(self, query: VinylQuery, max_pages: int = 2) -> list[ScrapedEdition]:
        res = self._results[query.album]
        if isinstance(res, Exception):
            raise res
        return res


class InMemoryHistoryRepo:
    def __init__(self, seed: list[PriceSnapshot] | None = None) -> None:
        self.snapshots: list[PriceSnapshot] = list(seed or [])
        self.saved_meta: dict[str, tuple[str, str, str, str]] = {}

    def save_snapshots(
        self,
        snapshots: list[PriceSnapshot],
        titles_by_asin: dict[str, tuple[str, str, str, str]],
    ) -> None:
        self.snapshots.extend(snapshots)
        self.saved_meta.update(titles_by_asin)

    def get_history(self, asin: ASIN) -> list[PriceSnapshot]:
        return sorted(
            [s for s in self.snapshots if s.asin == asin],
            key=lambda s: s.captured_at,
        )

    def get_editions_for_query(self, query: VinylQuery) -> list[ScrapedEdition]:
        return []


class FakeExternalHistory:
    def fetch_history(self, asin: ASIN) -> list[PriceSnapshot]:
        return []


class FakeExporter:
    def __init__(self) -> None:
        self.exported_reports: list[AlbumSearchReport] = []

    def export(self, reports: list[AlbumSearchReport], window: BlackFridayWindow) -> str:
        self.exported_reports = reports
        return "memory://report.json"


def test_use_case_filters_non_vinyl_deduplicates_and_ranks_editions() -> None:
    window = BlackFridayWindow(
        start=datetime(2026, 11, 20, tzinfo=UTC).date(),
        end=datetime(2026, 11, 30, tzinfo=UTC).date(),
        pre_bf_days=30,
    )
    query = VinylQuery(
        artist="Michael Jackson",
        album="Thriller",
        max_price_brl=Money.brl("350.00"),
        preferred_editions=("180g", "40th Anniversary"),
    )
    now = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
    pre_bf = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)

    # Seed pre-BF history for B000THR040
    repo = InMemoryHistoryRepo(
        seed=[
            PriceSnapshot(
                asin=ASIN("B000THR040"),
                price=Money.brl("340.00"),
                captured_at=pre_bf,
                source="amazon_br",
            )
        ]
    )
    scraper = FakeScraper(
        {
            "Thriller": [
                ScrapedEdition(
                    asin=ASIN("B000THR040"),
                    title="Michael Jackson - Thriller 40th Anniversary [Vinil 180g]",
                    url="https://www.amazon.com.br/dp/B000THR040",
                    current_price=Money.brl("220.00"),
                    list_price=Money.brl("340.00"),
                    captured_at=now,
                    is_prime=True,
                    rating=4.9,
                    review_count=800,
                ),
                # Duplicate ASIN should be deduplicated
                ScrapedEdition(
                    asin=ASIN("B000THR040"),
                    title="Michael Jackson - Thriller 40th Anniversary [Vinil 180g]",
                    url="https://www.amazon.com.br/dp/B000THR040",
                    current_price=Money.brl("220.00"),
                    captured_at=now,
                ),
                # Non-vinyl CD should be filtered out
                ScrapedEdition(
                    asin=ASIN("B000THR0CD"),
                    title="Michael Jackson - Thriller (CD Álbum)",
                    url="https://www.amazon.com.br/dp/B000THR0CD",
                    current_price=Money.brl("49.90"),
                    captured_at=now,
                ),
                # Second valid vinyl edition
                ScrapedEdition(
                    asin=ASIN("B000THRSTD"),
                    title="Michael Jackson - Thriller [Disco de Vinil]",
                    url="https://www.amazon.com.br/dp/B000THRSTD",
                    current_price=Money.brl("260.00"),
                    captured_at=now,
                ),
            ]
        }
    )
    exporter = FakeExporter()

    use_case = ScrapeAndAnalyzeVinylsUseCase(
        catalog_reader=FakeCatalogReader(window, [query]),
        scraper=scraper,
        history_repo=repo,
        external_history=FakeExternalHistory(),
        exporter=exporter,
    )

    result = use_case.execute(max_pages=1, scrape=True)

    assert len(result.reports) == 1
    report = result.reports[0]
    assert len(report.editions) == 2
    assert report.best_cost_benefit is not None
    assert report.best_cost_benefit.asin.value == "B000THR040"
    assert report.best_cost_benefit.bf_comparison.is_real_deal is True
    assert result.output_path == "memory://report.json"


def test_use_case_handles_captcha_block_gracefully() -> None:
    window = BlackFridayWindow(
        start=datetime(2026, 11, 20, tzinfo=UTC).date(),
        end=datetime(2026, 11, 30, tzinfo=UTC).date(),
        pre_bf_days=30,
    )
    q1 = VinylQuery(artist="Michael Jackson", album="Thriller")
    q2 = VinylQuery(artist="Pink Floyd", album="The Dark Side of the Moon")

    scraper = FakeScraper(
        {
            "Thriller": ScraperBlockedError("Michael Jackson Thriller", "CAPTCHA detected"),
            "The Dark Side of the Moon": [],
        }
    )
    exporter = FakeExporter()
    use_case = ScrapeAndAnalyzeVinylsUseCase(
        catalog_reader=FakeCatalogReader(window, [q1, q2]),
        scraper=scraper,
        history_repo=InMemoryHistoryRepo(),
        external_history=FakeExternalHistory(),
        exporter=exporter,
    )

    events: list[tuple[int, int, str, bool]] = []
    result = use_case.execute(
        max_pages=1,
        scrape=True,
        on_progress=lambda idx, total, q, rep: events.append(
            (idx, total, q.album, rep is not None)
        ),
    )

    assert len(events) == 4
    assert len(result.reports) == 2
    assert result.reports[0].blocked is True
    assert "CAPTCHA" in (result.reports[0].error_message or "")
    assert result.reports[1].blocked is False
