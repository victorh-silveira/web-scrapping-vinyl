from datetime import UTC, datetime
from decimal import Decimal

from vinyl_scraper.domain.entities import VinylQuery
from vinyl_scraper.domain.services import PriceAnalyticsService
from vinyl_scraper.domain.value_objects import (
    ASIN,
    BlackFridayWindow,
    EditionInfo,
    Money,
    PriceSnapshot,
)


def _snapshot(asin: str, price: str, dt: datetime, list_price: str | None = None) -> PriceSnapshot:
    return PriceSnapshot(
        asin=ASIN(asin),
        price=Money.brl(price),
        list_price=Money.brl(list_price) if list_price else None,
        captured_at=dt,
        source="amazon_br",
        is_prime=True,
    )


def test_price_analytics_computes_mean_median_and_real_bf_deal() -> None:
    service = PriceAnalyticsService()
    window = BlackFridayWindow(
        start=datetime(2026, 11, 20, tzinfo=UTC).date(),
        end=datetime(2026, 11, 30, tzinfo=UTC).date(),
        pre_bf_days=30,
    )
    asin = "B000000001"
    history = [
        _snapshot(asin, "300.00", datetime(2026, 10, 15, tzinfo=UTC)),
        _snapshot(asin, "320.00", datetime(2026, 11, 5, tzinfo=UTC)),
        _snapshot(asin, "310.00", datetime(2026, 11, 15, tzinfo=UTC)),
        _snapshot(asin, "210.00", datetime(2026, 11, 25, tzinfo=UTC), list_price="320.00"),
    ]

    stats = service.compute_stats(history)
    assert stats.sample_count == 4
    assert stats.min_price == Money.brl("210.00")
    assert stats.max_price == Money.brl("320.00")
    assert stats.mean_price == Money.brl("285.00")
    assert stats.median_price == Money.brl("305.00")

    bf = service.compare_black_friday(
        snapshots=history,
        current_price=Money.brl("210.00"),
        list_price=Money.brl("320.00"),
        stats=stats,
        window=window,
    )
    assert bf.pre_bf_mean_price == Money.brl("315.00")
    assert bf.pre_bf_last_price == Money.brl("310.00")
    assert bf.bf_price == Money.brl("210.00")
    assert bf.discount_vs_pre_bf_pct == Decimal("32.26")
    assert bf.is_real_deal is True


def test_price_analytics_detects_fake_black_friday_discount() -> None:
    service = PriceAnalyticsService()
    window = BlackFridayWindow(
        start=datetime(2026, 11, 20, tzinfo=UTC).date(),
        end=datetime(2026, 11, 30, tzinfo=UTC).date(),
        pre_bf_days=30,
    )
    asin = "B000000002"
    history = [
        _snapshot(asin, "200.00", datetime(2026, 11, 1, tzinfo=UTC)),
        _snapshot(asin, "205.00", datetime(2026, 11, 10, tzinfo=UTC)),
        _snapshot(asin, "220.00", datetime(2026, 11, 25, tzinfo=UTC), list_price="440.00"),
    ]
    stats = service.compute_stats(history)
    bf = service.compare_black_friday(
        snapshots=history,
        current_price=Money.brl("220.00"),
        list_price=Money.brl("440.00"),
        stats=stats,
        window=window,
    )
    assert bf.is_real_deal is False
    assert bf.discount_vs_pre_bf_pct < Decimal("0")


def test_cost_benefit_rewards_real_discount_and_preferred_edition() -> None:
    service = PriceAnalyticsService()
    query = VinylQuery(
        artist="Michael Jackson",
        album="Thriller",
        max_price_brl=Money.brl("300.00"),
        preferred_editions=("180g", "40th Anniversary"),
    )
    window = BlackFridayWindow(
        start=datetime(2026, 11, 20, tzinfo=UTC).date(),
        end=datetime(2026, 11, 30, tzinfo=UTC).date(),
        pre_bf_days=30,
    )
    history = [
        _snapshot("B000000003", "320.00", datetime(2026, 11, 10, tzinfo=UTC)),
        _snapshot("B000000003", "220.00", datetime(2026, 11, 25, tzinfo=UTC)),
    ]
    stats = service.compute_stats(history)
    bf = service.compare_black_friday(
        snapshots=history,
        current_price=Money.brl("220.00"),
        list_price=Money.brl("320.00"),
        stats=stats,
        window=window,
    )
    ed_info = EditionInfo(
        is_vinyl=True,
        edition_label="40th Anniversary (180g)",
        is_180g=True,
        is_anniversary=True,
    )
    score = service.compute_cost_benefit(
        query=query,
        current_price=Money.brl("220.00"),
        stats=stats,
        bf_comparison=bf,
        edition_info=ed_info,
        is_prime=True,
        rating=4.8,
        review_count=1200,
    )
    assert score.total_score >= 60.0
