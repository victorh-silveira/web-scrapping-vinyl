"""Entidades de domínio e raízes de agregação."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from vinyl_scraper.domain.value_objects import (
    ASIN,
    BlackFridayComparison,
    CostBenefitScore,
    EditionInfo,
    Money,
    PriceStats,
)


@dataclass(frozen=True)
class VinylQuery:
    """Especificação de busca de um disco de vinil a partir do catálogo JSON do usuário."""

    artist: str
    album: str
    max_price_brl: Money | None = None
    preferred_editions: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()

    @property
    def search_term(self) -> str:
        """Constrói uma string limpa de busca na Amazon BR."""
        sanitized = self.album.replace(":", " ").replace("!", " ").replace("?", " ")
        clean_album = " ".join(tok for tok in sanitized.split() if tok.lower() != "ost")
        artist_lower = self.artist.strip().lower()
        if artist_lower in {"various artists", "vários artistas"} or "/" in self.artist:
            return f"{clean_album} vinil".strip()
        return f"{self.artist} {clean_album} vinil".strip()


@dataclass(frozen=True)
class ScrapedEdition:
    """Listagem bruta de vinil coletada da Amazon BR antes do enriquecimento histórico."""

    asin: ASIN
    title: str
    url: str
    current_price: Money
    captured_at: datetime
    list_price: Money | None = None
    is_prime: bool = False
    rating: float | None = None
    review_count: int = 0
    seller: str | None = None
    format_hint: str | None = None


@dataclass
class VinylEdition:
    """Raiz de agregação representando uma edição/versão específica de vinil de um álbum."""

    asin: ASIN
    title: str
    url: str
    edition_info: EditionInfo
    current_price: Money
    list_price: Money | None
    is_prime: bool
    rating: float | None
    review_count: int
    seller: str | None
    stats: PriceStats
    bf_comparison: BlackFridayComparison
    cost_benefit: CostBenefitScore


@dataclass
class AlbumSearchReport:
    """Resultados agregados contendo todas as edições de vinil encontradas para um álbum."""

    query: VinylQuery
    editions: list[VinylEdition] = field(default_factory=list)
    blocked: bool = False
    error_message: str | None = None

    @property
    def best_cost_benefit(self) -> VinylEdition | None:
        """Retorna a edição com o maior score de custo-benefício."""
        if not self.editions:
            return None
        return max(self.editions, key=lambda e: e.cost_benefit.total_score)

    @property
    def best_promotion(self) -> VinylEdition | None:
        """Retorna a edição com o maior desconto real frente à mediana/Pré-BF."""
        if not self.editions:
            return None
        return max(
            self.editions,
            key=lambda e: (
                e.bf_comparison.is_real_deal,
                e.bf_comparison.discount_vs_median_pct,
                e.bf_comparison.discount_vs_pre_bf_pct,
            ),
        )
