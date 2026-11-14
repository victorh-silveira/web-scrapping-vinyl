"""Objetos de valor imutáveis do domínio."""

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
    """Valor monetário imutável em BRL (ou moeda explícita)."""

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
        """Cria uma instância de Money em BRL a partir de um valor numérico ou string."""
        try:
            dec = value if isinstance(value, Decimal) else Decimal(str(value))
        except InvalidOperation as exc:
            raise InvalidMoneyError(f"Invalid monetary value: {value!r}") from exc
        return cls(amount=dec, currency="BRL")

    def discount_percentage_from(self, original: Money) -> Decimal:
        """Retorna o desconto percentual em relação a `original` (negativo se maior)."""
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
    """Amazon Standard Identification Number (10 caracteres alfanuméricos)."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not _ASIN_PATTERN.match(normalized):
            raise InvalidAsinError(f"Invalid ASIN: {self.value!r}")
        object.__setattr__(self, "value", normalized)


class PriceWindowTag(StrEnum):
    """Classificação temporal para análise de preços de Black Friday."""

    REGULAR = "regular"
    PRE_BLACK_FRIDAY = "pre_black_friday"
    BLACK_FRIDAY = "black_friday"


@dataclass(frozen=True)
class BlackFridayWindow:
    """Intervalo de datas que define a Black Friday e a janela de comparação anterior."""

    start: date
    end: date
    pre_bf_days: int = 30

    def classify(self, timestamp: datetime) -> PriceWindowTag:
        """Classifica um timestamp em REGULAR, PRE_BLACK_FRIDAY ou BLACK_FRIDAY."""
        day = timestamp.date()
        if self.start <= day <= self.end:
            return PriceWindowTag.BLACK_FRIDAY
        pre_start = self.start - timedelta(days=self.pre_bf_days)
        if pre_start <= day < self.start:
            return PriceWindowTag.PRE_BLACK_FRIDAY
        return PriceWindowTag.REGULAR


@dataclass(frozen=True)
class EditionInfo:
    """Atributos normalizados de edição de vinil extraídos do título do produto."""

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
    """Observação pontual de preço para um ASIN específico."""

    asin: ASIN
    price: Money
    captured_at: datetime
    source: str
    list_price: Money | None = None
    seller: str | None = None
    is_prime: bool = False


@dataclass(frozen=True)
class PriceStats:
    """Estatísticas descritivas sobre snapshots históricos de preços."""

    min_price: Money
    max_price: Money
    mean_price: Money
    median_price: Money
    sample_count: int


@dataclass(frozen=True)
class BlackFridayComparison:
    """Comparação entre preços Pré-Black Friday e preço de Black Friday / atual."""

    pre_bf_mean_price: Money | None
    pre_bf_last_price: Money | None
    bf_price: Money | None
    discount_vs_pre_bf_pct: Decimal
    discount_vs_median_pct: Decimal
    is_real_deal: bool
    deal_verdict: str


@dataclass(frozen=True)
class CostBenefitScore:
    """Score ponderado de custo-benefício (0.0 a 100.0) com detalhamento por componente."""

    total_score: float
    discount_score: float
    median_score: float
    edition_score: float
    trust_score: float
