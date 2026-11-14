from datetime import UTC, datetime
from decimal import Decimal

from vinyl_scraper.domain.edition_classifier import EditionClassifier
from vinyl_scraper.domain.entities import VinylQuery
from vinyl_scraper.domain.price_analytics import PriceAnalyticsService
from vinyl_scraper.domain.value_objects import (
    ASIN,
    BlackFridayWindow,
    Money,
    PriceSnapshot,
)
from vinyl_scraper.infrastructure.scrapers.amazon_br_parser import AmazonBrSearchParser


def test_vinyl_query_search_term_cleans_ost_and_various_artists() -> None:
    q1 = VinylQuery(artist="Various Artists", album="Dirty Dancing OST")
    q2 = VinylQuery(artist="Lorne Balfe / Hans Zimmer", album="Top Gun: Maverick OST")
    q3 = VinylQuery(artist="Michael Jackson", album="Thriller")

    assert q1.search_term == "Dirty Dancing vinil"
    assert q2.search_term == "Top Gun Maverick vinil"
    assert q3.search_term == "Michael Jackson Thriller vinil"


def test_classifier_uses_format_hint_rejects_tribute_and_supports_aliases() -> None:
    clf = EditionClassifier()

    bon_jovi = VinylQuery(artist="Bon Jovi", album="Slippery When Wet")
    assert (
        clf.classify("Slippery When Wet", bon_jovi, format_hint="Disco de Vinil").is_vinyl is True
    )
    assert clf.classify("Slippery When Wet", bon_jovi, format_hint="CD de áudio").is_vinyl is False

    thriller = VinylQuery(artist="Michael Jackson", album="Thriller")
    tribute = clf.classify("THRILLER - A METAL TRIBUTE TO MICHAEL JACKSON (RED VINYL)", thriller)
    assert tribute.is_vinyl is False
    assert tribute.edition_label == "Tribute"

    boston = VinylQuery(artist="Boston", album="Boston")
    assert clf.classify("Boston Hardcore '89-91 [Disco de Vinil]", boston).is_vinyl is False
    assert clf.classify("Boston [Disco de Vinil]", boston).is_vinyl is True

    whitesnake = VinylQuery(artist="Whitesnake", album="1987", aliases=("Whitesnake",))
    assert clf.classify("Whitesnake[LP]", whitesnake).is_vinyl is True


def test_parser_ignores_installment_prices_and_extracts_format_hint() -> None:
    html = """
    <div data-asin="B000BONJOV" data-component-type="s-search-result">
      <h2><a href="/dp/B000BONJOV"><span>Slippery When Wet</span></a></h2>
      <a class="a-size-base a-link-normal" href="/dp/B000BONJOV">Disco de Vinil</a>
      <span class="a-price"><span class="a-offscreen">R$ 269,29</span></span>
      <span class="a-price a-text-price"><span class="a-offscreen">R$ 44,88</span></span>
    </div>
    <div data-asin="B000WHITE1" data-component-type="s-search-result">
      <h2><a href="/dp/B000WHITE1"><span>Whitesnake[LP]</span></a></h2>
      <span class="a-price"><span class="a-offscreen">R$ 306,25</span></span>
      <span class="a-price a-text-price" data-a-strike="true">
        <span class="a-offscreen">R$ 419,14</span>
      </span>
    </div>
    <div data-asin="B000LOWER1" data-component-type="s-search-result">
      <h2><a href="/dp/B000LOWER1"><span>Bad Strike [Vinil]</span></a></h2>
      <span class="a-price"><span class="a-offscreen">R$ 300,00</span></span>
      <span class="a-price a-text-price" data-a-strike="true">
        <span class="a-offscreen">R$ 100,00</span>
      </span>
    </div>
    """
    parser = AmazonBrSearchParser()
    items = parser.parse_search_results(html, datetime(2026, 11, 14, 12, 0, tzinfo=UTC))
    assert len(items) == 3

    assert items[0].format_hint == "Disco de Vinil"
    assert items[0].list_price is None

    assert items[1].current_price == Money.brl("306.25")
    assert items[1].list_price == Money.brl("419.14")

    assert items[2].list_price is None


def test_first_run_in_pre_bf_window_uses_list_price_for_discount() -> None:
    svc = PriceAnalyticsService()
    window = BlackFridayWindow(
        start=datetime(2026, 11, 20, tzinfo=UTC).date(),
        end=datetime(2026, 11, 30, tzinfo=UTC).date(),
        pre_bf_days=30,
    )
    snap = PriceSnapshot(
        asin=ASIN("B000WHITE1"),
        price=Money.brl("306.25"),
        list_price=Money.brl("419.14"),
        captured_at=datetime(2026, 11, 14, 12, 0, tzinfo=UTC),
        source="amazon_br",
    )
    stats = svc.compute_stats([snap])
    bf = svc.compare_black_friday(
        snapshots=[snap],
        current_price=Money.brl("306.25"),
        list_price=Money.brl("419.14"),
        stats=stats,
        window=window,
    )
    assert bf.pre_bf_last_price == Money.brl("419.14")
    assert bf.discount_vs_pre_bf_pct == Decimal("26.93")
    assert bf.is_real_deal is True
