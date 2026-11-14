from datetime import UTC, datetime
from decimal import Decimal

import pytest

from vinyl_scraper.domain.exceptions import InvalidAsinError, InvalidMoneyError
from vinyl_scraper.domain.value_objects import (
    ASIN,
    BlackFridayWindow,
    Money,
    PriceWindowTag,
)


def test_money_creation_and_rounding() -> None:
    price = Money.brl("199.995")
    assert price.amount == Decimal("200.00")
    assert price.currency == "BRL"
    assert str(price) == "R$ 200.00"


def test_money_rejects_negative() -> None:
    with pytest.raises(InvalidMoneyError):
        Money.brl("-10.00")


def test_money_discount_percentage() -> None:
    original = Money.brl("200.00")
    discounted = Money.brl("150.00")
    assert discounted.discount_percentage_from(original) == Decimal("25.00")


def test_money_discount_percentage_when_more_expensive() -> None:
    original = Money.brl("200.00")
    higher = Money.brl("220.00")
    assert higher.discount_percentage_from(original) == Decimal("-10.00")


def test_asin_validation_and_normalization() -> None:
    asin = ASIN("b0b6x9v123")
    assert asin.value == "B0B6X9V123"


@pytest.mark.parametrize("bad_asin", ["", "123", "B0B6X9V1234", "B0B6X9V12!"])
def test_asin_rejects_invalid_values(bad_asin: str) -> None:
    with pytest.raises(InvalidAsinError):
        ASIN(bad_asin)


def test_black_friday_window_classification() -> None:
    window = BlackFridayWindow(
        start=datetime(2026, 11, 20, 0, 0, tzinfo=UTC).date(),
        end=datetime(2026, 11, 30, 23, 59, tzinfo=UTC).date(),
        pre_bf_days=30,
    )
    assert window.classify(datetime(2026, 10, 15, tzinfo=UTC)) == PriceWindowTag.REGULAR
    assert window.classify(datetime(2026, 11, 1, tzinfo=UTC)) == PriceWindowTag.PRE_BLACK_FRIDAY
    assert window.classify(datetime(2026, 11, 25, tzinfo=UTC)) == PriceWindowTag.BLACK_FRIDAY
    assert window.classify(datetime(2026, 12, 5, tzinfo=UTC)) == PriceWindowTag.REGULAR
