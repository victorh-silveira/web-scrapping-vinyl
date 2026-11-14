from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from vinyl_scraper.application.use_cases import ScrapeAndAnalyzeVinylsUseCase
from vinyl_scraper.domain.edition_classifier import EditionClassifier
from vinyl_scraper.domain.entities import (
    AlbumSearchReport,
    ScrapedEdition,
    VinylEdition,
    VinylQuery,
)
from vinyl_scraper.domain.exceptions import InvalidMoneyError
from vinyl_scraper.domain.price_analytics import PriceAnalyticsService
from vinyl_scraper.domain.value_objects import (
    ASIN,
    BlackFridayComparison,
    BlackFridayWindow,
    CostBenefitScore,
    EditionInfo,
    Money,
    PriceSnapshot,
    PriceStats,
)
from vinyl_scraper.infrastructure.scrapers import playwright_amazon_scraper as scraper_mod
from vinyl_scraper.infrastructure.scrapers.amazon_br_parser import (
    AmazonBrSearchParser,
    parse_brl_price,
)
from vinyl_scraper.infrastructure.scrapers.playwright_amazon_scraper import PlaywrightAmazonScraper


def test_value_objects_edge_cases() -> None:
    with pytest.raises(InvalidMoneyError):
        Money(amount="10.00")  # type: ignore[arg-type]
    with pytest.raises(InvalidMoneyError):
        Money.brl("not-a-number")
    assert Money.brl("100.00").discount_percentage_from(Money.brl("0.00")) == Decimal("0.00")


def test_entities_empty_and_populated_best_properties() -> None:
    q = VinylQuery(artist="Artist", album="Album")
    empty = AlbumSearchReport(query=q, editions=[])
    assert empty.best_cost_benefit is None
    assert empty.best_promotion is None

    ed = VinylEdition(
        asin=ASIN("B000000001"),
        title="Artist - Album [Vinil]",
        url="https://www.amazon.com.br/dp/B000000001",
        edition_info=EditionInfo(is_vinyl=True, edition_label="Standard LP"),
        current_price=Money.brl("100.00"),
        list_price=None,
        is_prime=False,
        rating=None,
        review_count=0,
        seller=None,
        stats=PriceStats(
            min_price=Money.brl("100.00"),
            max_price=Money.brl("100.00"),
            mean_price=Money.brl("100.00"),
            median_price=Money.brl("100.00"),
            sample_count=1,
        ),
        bf_comparison=BlackFridayComparison(
            pre_bf_mean_price=None,
            pre_bf_last_price=None,
            bf_price=Money.brl("100.00"),
            discount_vs_pre_bf_pct=Decimal("0.00"),
            discount_vs_median_pct=Decimal("0.00"),
            is_real_deal=False,
            deal_verdict="Primeiro registro",
        ),
        cost_benefit=CostBenefitScore(
            total_score=10.0,
            discount_score=0.0,
            median_score=0.0,
            edition_score=5.0,
            trust_score=5.0,
        ),
    )
    populated = AlbumSearchReport(query=q, editions=[ed])
    assert populated.best_promotion is ed


def test_classifier_unknown_format_anniversary_and_short_album() -> None:
    clf = EditionClassifier()
    q = VinylQuery(artist="Michael Jackson", album="Thriller")
    assert clf.classify("Michael Jackson - Thriller", q).edition_label == "Unknown Format"
    ann = clf.classify("Michael Jackson - Thriller Anniversary Edition [Vinil]", q)
    assert ann.is_vinyl is True
    assert "Anniversary Edition" in ann.edition_label

    short_q = VinylQuery(artist="Led Zeppelin", album="IV")
    assert clf.classify("Led Zeppelin - IV [Vinil]", short_q).is_vinyl is True
    assert clf.classify("Other Band - IV [Vinil]", short_q).is_vinyl is False


def test_price_analytics_edge_branches() -> None:
    svc = PriceAnalyticsService()
    empty_stats = svc.compute_stats([])
    assert empty_stats.sample_count == 0

    window = BlackFridayWindow(
        start=datetime(2026, 11, 20, tzinfo=UTC).date(),
        end=datetime(2026, 11, 30, tzinfo=UTC).date(),
        pre_bf_days=30,
    )
    q = VinylQuery(
        artist="A",
        album="Album",
        max_price_brl=Money.brl("150.00"),
        preferred_editions=("Picture Disc",),
    )
    snaps = [
        PriceSnapshot(
            asin=ASIN("B000000001"),
            price=Money.brl("200.00"),
            captured_at=datetime(2026, 11, 5, tzinfo=UTC),
            source="amazon_br",
        ),
        PriceSnapshot(
            asin=ASIN("B000000001"),
            price=Money.brl("185.00"),
            captured_at=datetime(2026, 11, 25, tzinfo=UTC),
            source="amazon_br",
        ),
    ]
    stats = svc.compute_stats(snaps)
    bf = svc.compare_black_friday(
        snapshots=snaps,
        current_price=Money.brl("185.00"),
        list_price=None,
        stats=stats,
        window=window,
    )
    assert bf.deal_verdict == "Boa oferta"

    score = svc.compute_cost_benefit(
        query=q,
        current_price=Money.brl("185.00"),
        stats=stats,
        bf_comparison=bf,
        edition_info=EditionInfo(
            is_vinyl=True,
            edition_label="2LP Remastered",
            is_double_lp=True,
            is_remastered=True,
        ),
        is_prime=False,
        rating=4.0,
        review_count=20,
    )
    assert score.total_score > 0.0

    bf_regular = svc.compare_black_friday(
        snapshots=snaps,
        current_price=Money.brl("198.00"),
        list_price=None,
        stats=stats,
        window=window,
    )
    assert bf_regular.deal_verdict == "Preço dentro da média histórica"

    single_pre_bf = [snaps[0]]
    bf_single = svc.compare_black_friday(
        snapshots=single_pre_bf,
        current_price=Money.brl("200.00"),
        list_price=None,
        stats=svc.compute_stats(single_pre_bf),
        window=window,
    )
    assert bf_single.pre_bf_last_price == Money.brl("200.00")


def test_use_case_merge_snapshots_fallback_when_empty() -> None:
    uc = ScrapeAndAnalyzeVinylsUseCase(
        catalog_reader=MagicMock(),
        scraper=MagicMock(),
        history_repo=MagicMock(),
        external_history=MagicMock(),
        exporter=MagicMock(),
    )
    item = ScrapedEdition(
        asin=ASIN("B000000001"),
        title="Album [Vinil]",
        url="https://www.amazon.com.br/dp/B000000001",
        current_price=Money.brl("100.00"),
        captured_at=datetime(2026, 11, 25, tzinfo=UTC),
    )
    merged = uc._merge_snapshots([], [], item)
    assert len(merged) == 1
    assert merged[0].price == Money.brl("100.00")


def test_parser_edge_cases_and_multipage_scraper(monkeypatch: pytest.MonkeyPatch) -> None:
    assert parse_brl_price("   ") is None
    assert parse_brl_price("100") == Money.brl("100.00")
    assert parse_brl_price("1,2,3") is None

    html = """
    <div data-asin="INVALID" data-component-type="s-search-result"></div>
    <div data-asin="B000000001" data-component-type="s-search-result"></div>
    <div data-asin="B000000002" data-component-type="s-search-result">
      <h2><span>   </span></h2>
    </div>
    <div data-asin="B000000003" data-component-type="s-search-result">
      <h2><span>No Price [Vinil]</span></h2>
    </div>
    <div data-asin="B000000004" data-component-type="s-search-result">
      <h2><span>Multi Price [Vinil]</span></h2>
      <a class="a-size-base a-link-normal" href="/dp/B000000004">Mais ofertas</a>
      <span class="a-price"><span>no offscreen</span></span>
      <span class="a-price"><span class="a-offscreen">bad</span></span>
      <span class="a-price a-text-price" data-a-strike="true">
        <span class="a-offscreen">R$ 300,00</span>
      </span>
      <span class="a-price a-text-price" data-a-strike="true">
        <span class="a-offscreen">R$ 350,00</span>
      </span>
      <span class="a-price"><span class="a-offscreen">R$ 200,00</span></span>
      <span class="a-price"><span class="a-offscreen">R$ 210,00</span></span>
      <span class="a-icon-alt">sem nota</span>
      <span class="a-size-base s-underline-text">abc</span>
    </div>
    """
    parser = AmazonBrSearchParser()
    parsed = parser.parse_search_results(html, datetime(2026, 11, 25, tzinfo=UTC))
    assert len(parsed) == 1
    assert parsed[0].asin.value == "B000000004"
    assert parsed[0].current_price == Money.brl("200.00")
    assert parsed[0].list_price == Money.brl("300.00")

    page = MagicMock()
    page.content.side_effect = [html, html]
    context = MagicMock()
    context.new_page.return_value = page
    browser = MagicMock()
    browser.new_context.return_value = context
    pw_instance = MagicMock()
    pw_instance.chromium.launch.return_value = browser
    cm = MagicMock()
    cm.__enter__.return_value = pw_instance
    cm.__exit__.return_value = False
    monkeypatch.setattr(scraper_mod, "sync_playwright", lambda: cm)
    monkeypatch.setattr(scraper_mod.time, "sleep", lambda _s: None)

    scraper = PlaywrightAmazonScraper(min_delay_sec=0.0, max_delay_sec=0.0)
    res = scraper.search_vinyl_editions(VinylQuery(artist="A", album="B"), max_pages=2)
    assert len(res) == 2
