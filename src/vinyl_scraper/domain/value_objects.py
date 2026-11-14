"""Immutable Domain Value Objects."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from enum import StrEnum

from vinyl_scraper.domain.exceptions import InvalidAsinError, InvalidMoneyError

_ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")
_TWO_PLACES = Decimal("0.01")


@dataclass(frozen=True, order=True)
class Money:
    """Immutable monetary value in BRL (or explicit currency)."""

    amount: Decimal
    currency: str = "BRL"

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise InvalidMoneyError("Money amount must be a Decimal.")
        if self.amount < Decimal("0"):
            raise InvalidMoneyError(f"Money amount cannot be negative: {self.amount}")
        quantized = self.amount.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", quantized)

    @classmethod
    def brl(cls, value: Decimal | str | int | float) -> Money:
        """Create a BRL Money instance from a numeric or string value."""
        try:
            dec = value if isinstance(value, Decimal) else Decimal(str(value))
        except InvalidOperation as exc:
            raise InvalidMoneyError(f"Invalid monetary value: {value!r}") from exc
        return cls(amount=dec, currency="BRL")

    def discount_percentage_from(self, original: Money) -> Decimal:
        """Return percentage discount relative to `original` (negative if higher)."""
        if original.amount <= Decimal("0"):
            return Decimal("0.00")
        diff = original.amount - self.amount
        pct = (diff / original.amount) * Decimal("100")
        return pct.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

    def __str__(self) -> str:
        symbol = "R$" if self.currency == "BRL" else self.currency
        return f"{symbol} {self.amount:.2f}"


@dataclass(frozen=True)
class ASIN:
    """Amazon Standard Identification Number (10 alphanumeric chars)."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not _ASIN_PATTERN.match(normalized):
            raise InvalidAsinError(f"Invalid ASIN: {self.value!r}")
        object.__setattr__(self, "value", normalized)


class PriceWindowTag(StrEnum):
    """Temporal classification for Black Friday price analysis."""

    REGULAR = "regular"
    PRE_BLACK_FRIDAY = "pre_black_friday"
    BLACK_FRIDAY = "black_friday"


@dataclass(frozen=True)
class BlackFridayWindow:
    """Date range defining Black Friday and its preceding comparison window."""

    start: date
    end: date
    pre_bf_days: int = 30

    def classify(self, timestamp: datetime) -> PriceWindowTag:
        """Classify a timestamp into REGULAR, PRE_BLACK_FRIDAY, or BLACK_FRIDAY."""
        day = timestamp.date()
        if self.start <= day <= self.end:
            return PriceWindowTag.BLACK_FRIDAY
        pre_start = self.start - timedelta(days=self.pre_bf_days)
        if pre_start <= day < self.start:
            return PriceWindowTag.PRE_BLACK_FRIDAY
        return PriceWindowTag.REGULAR


@dataclass(frozen=True)
class EditionInfo:
    """Normalized vinyl edition attributes extracted from a product title."""

    is_vinyl: bool
    edition_label: str
    is_180g: bool = False
    is_double_lp: bool = False
    is_picture_disc: bool = False
    is_colored: bool = False
    is_anniversary: bool = False
    is_import: bool = False
    is_remastered: bool = False


@dataclass(frozen=True)
class PriceSnapshot:
    """Point-in-time price observation for a specific ASIN."""

    asin: ASIN
    price: Money
    captured_at: datetime
    source: str
    list_price: Money | None = None
    seller: str | None = None
    is_prime: bool = False


@dataclass(frozen=True)
class PriceStats:
    """Descriptive statistics over historical price snapshots."""

    min_price: Money
    max_price: Money
    mean_price: Money
    median_price: Money
    sample_count: int


@dataclass(frozen=True)
class BlackFridayComparison:
    """Comparison between Pre-Black Friday prices and Black Friday / current price."""

    pre_bf_mean_price: Money | None
    pre_bf_last_price: Money | None
    bf_price: Money | None
    discount_vs_pre_bf_pct: Decimal
    discount_vs_median_pct: Decimal
    is_real_deal: bool
    deal_verdict: str


@dataclass(frozen=True)
class CostBenefitScore:
    """Weighted cost-benefit score (0.0 to 100.0) with component breakdown."""

    total_score: float
    discount_score: float
    median_score: float
    edition_score: float
    trust_score: float
