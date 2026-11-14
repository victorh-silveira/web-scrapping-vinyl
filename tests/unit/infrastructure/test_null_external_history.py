from vinyl_scraper.domain.value_objects import ASIN
from vinyl_scraper.infrastructure.external.null_external_history import NullExternalPriceHistory


def test_null_external_history_returns_empty_list() -> None:
    adapter = NullExternalPriceHistory()
    assert adapter.fetch_history(ASIN("B0B6X9V40A")) == []
