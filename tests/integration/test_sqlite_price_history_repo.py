from datetime import UTC, datetime

from vinyl_scraper.domain.entities import VinylQuery
from vinyl_scraper.domain.value_objects import ASIN, Money, PriceSnapshot
from vinyl_scraper.infrastructure.persistence.sqlite_price_history_repo import (
    SqlitePriceHistoryRepository,
)


def test_sqlite_repo_persists_and_queries_history() -> None:
    repo = SqlitePriceHistoryRepository(":memory:")
    asin = ASIN("B0B6X9V40A")
    t1 = datetime(2026, 11, 1, 10, 0, tzinfo=UTC)
    t2 = datetime(2026, 11, 25, 10, 0, tzinfo=UTC)

    repo.save_snapshots(
        snapshots=[
            PriceSnapshot(
                asin=asin,
                price=Money.brl("320.00"),
                list_price=None,
                captured_at=t1,
                source="amazon_br",
                is_prime=True,
            ),
            PriceSnapshot(
                asin=asin,
                price=Money.brl("219.90"),
                list_price=Money.brl("320.00"),
                captured_at=t2,
                source="amazon_br",
                is_prime=True,
            ),
        ],
        titles_by_asin={
            "B0B6X9V40A": (
                "Michael Jackson - Thriller 40th Anniversary [Vinil 180g]",
                "Michael Jackson",
                "Thriller",
                "40th Anniversary / 180g",
            )
        },
    )

    history = repo.get_history(asin)
    assert len(history) == 2
    assert history[0].price == Money.brl("320.00")
    assert history[1].price == Money.brl("219.90")
    assert history[1].list_price == Money.brl("320.00")

    query = VinylQuery(artist="Michael Jackson", album="Thriller")
    editions = repo.get_editions_for_query(query)
    assert len(editions) == 1
    assert editions[0].asin == asin
    assert editions[0].current_price == Money.brl("219.90")
    repo.close()
