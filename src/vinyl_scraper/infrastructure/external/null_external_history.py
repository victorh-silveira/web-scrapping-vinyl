"""Adaptador NullObject padrão para ExternalPriceHistoryPort."""

from __future__ import annotations

from vinyl_scraper.domain.value_objects import ASIN, PriceSnapshot


class NullExternalPriceHistory:
    """Adaptador padrão sem operação para histórico externo (pronto para troca pela Keepa API)."""

    def fetch_history(self, asin: ASIN) -> list[PriceSnapshot]:
        """Retorna uma lista vazia quando nenhum rastreador externo está configurado."""
        return []
