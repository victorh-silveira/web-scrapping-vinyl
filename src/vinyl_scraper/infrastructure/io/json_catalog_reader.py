"""Adaptador leitor de catálogo JSON."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from vinyl_scraper.domain.entities import VinylQuery
from vinyl_scraper.domain.value_objects import BlackFridayWindow, Money


class JsonCatalogReader:
    """Carrega BlackFridayWindow e itens VinylQuery a partir de um arquivo JSON."""

    def __init__(
        self,
        path: str | Path,
        bf_start_override: date | None = None,
        bf_end_override: date | None = None,
        pre_bf_days_override: int | None = None,
    ) -> None:
        self._path = Path(path)
        self._bf_start_override = bf_start_override
        self._bf_end_override = bf_end_override
        self._pre_bf_days_override = pre_bf_days_override

    def load(self) -> tuple[BlackFridayWindow, list[VinylQuery]]:
        """Faz o parsing do catálogo JSON para objetos de domínio."""
        raw = json.loads(self._path.read_text(encoding="utf-8"))

        bf_cfg = raw.get("black_friday_window", {})
        today = date.today()
        default_start = date.fromisoformat(
            bf_cfg.get("start", (today - timedelta(days=5)).isoformat())
        )
        default_end = date.fromisoformat(bf_cfg.get("end", (today + timedelta(days=5)).isoformat()))
        pre_bf_days = int(
            self._pre_bf_days_override
            if self._pre_bf_days_override is not None
            else bf_cfg.get("pre_bf_days", 30)
        )

        window = BlackFridayWindow(
            start=self._bf_start_override or default_start,
            end=self._bf_end_override or default_end,
            pre_bf_days=pre_bf_days,
        )

        queries: list[VinylQuery] = []
        for entry in raw.get("vinyls", []):
            max_price_raw = entry.get("max_price_brl")
            max_price = Money.brl(max_price_raw) if max_price_raw is not None else None
            prefs = tuple(str(p) for p in entry.get("preferred_editions", []))
            aliases = tuple(str(a) for a in entry.get("aliases", []))
            queries.append(
                VinylQuery(
                    artist=str(entry["artist"]).strip(),
                    album=str(entry["album"]).strip(),
                    max_price_brl=max_price,
                    preferred_editions=prefs,
                    aliases=aliases,
                )
            )

        return window, queries
