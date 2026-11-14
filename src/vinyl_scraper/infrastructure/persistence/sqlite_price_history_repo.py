"""Repositório SQLite para snapshots locais de histórico de preços de vinis."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from vinyl_scraper.domain.entities import ScrapedEdition, VinylQuery
from vinyl_scraper.domain.value_objects import ASIN, Money, PriceSnapshot


class SqlitePriceHistoryRepository:
    """Armazena e consulta snapshots de preço com timestamp em SQLite."""

    def __init__(self, db_path: str | Path = "data/price_history.db") -> None:
        if str(db_path) != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS editions (
                    asin TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    album TEXT NOT NULL,
                    edition_label TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS price_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asin TEXT NOT NULL,
                    price_brl TEXT NOT NULL,
                    list_price_brl TEXT,
                    captured_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    seller TEXT,
                    is_prime INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (asin) REFERENCES editions(asin)
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_snapshots_asin_time "
                "ON price_snapshots(asin, captured_at)"
            )

    def save_snapshots(
        self,
        snapshots: list[PriceSnapshot],
        titles_by_asin: dict[str, tuple[str, str, str, str]],
    ) -> None:
        """Persiste novos snapshots de preço e atualiza metadados das edições."""
        now_iso = datetime.now().isoformat()
        with self._conn:
            for asin_str, (title, artist, album, label) in titles_by_asin.items():
                self._conn.execute(
                    """
                    INSERT INTO editions (asin, title, artist, album, edition_label, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(asin) DO UPDATE SET
                        title = excluded.title,
                        edition_label = excluded.edition_label,
                        updated_at = excluded.updated_at
                    """,
                    (asin_str, title, artist, album, label, now_iso),
                )

            for snap in snapshots:
                self._conn.execute(
                    """
                    INSERT INTO price_snapshots
                        (asin, price_brl, list_price_brl, captured_at, source, seller, is_prime)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snap.asin.value,
                        str(snap.price.amount),
                        str(snap.list_price.amount) if snap.list_price is not None else None,
                        snap.captured_at.isoformat(),
                        snap.source,
                        snap.seller,
                        1 if snap.is_prime else 0,
                    ),
                )

    def get_history(self, asin: ASIN) -> list[PriceSnapshot]:
        """Retorna todos os snapshots de `asin` ordenados cronologicamente."""
        rows = self._conn.execute(
            """
            SELECT asin, price_brl, list_price_brl, captured_at, source, seller, is_prime
            FROM price_snapshots
            WHERE asin = ?
            ORDER BY captured_at ASC
            """,
            (asin.value,),
        ).fetchall()

        return [
            PriceSnapshot(
                asin=ASIN(row["asin"]),
                price=Money.brl(row["price_brl"]),
                list_price=Money.brl(row["list_price_brl"]) if row["list_price_brl"] else None,
                captured_at=datetime.fromisoformat(row["captured_at"]),
                source=row["source"],
                seller=row["seller"],
                is_prime=bool(row["is_prime"]),
            )
            for row in rows
        ]

    def get_editions_for_query(self, query: VinylQuery) -> list[ScrapedEdition]:
        """Retorna o ScrapedEdition mais recente armazenado por ASIN correspondente a `query`."""
        rows = self._conn.execute(
            """
            SELECT e.asin, e.title,
                   s.price_brl, s.list_price_brl, s.captured_at, s.seller, s.is_prime
            FROM editions e
            JOIN price_snapshots s ON s.asin = e.asin
            WHERE LOWER(e.artist) = LOWER(?) AND LOWER(e.album) = LOWER(?)
              AND s.id = (
                  SELECT s2.id FROM price_snapshots s2
                  WHERE s2.asin = e.asin
                  ORDER BY s2.captured_at DESC, s2.id DESC
                  LIMIT 1
              )
            """,
            (query.artist, query.album),
        ).fetchall()

        return [
            ScrapedEdition(
                asin=ASIN(row["asin"]),
                title=row["title"],
                url=f"https://www.amazon.com.br/dp/{row['asin']}",
                current_price=Money.brl(row["price_brl"]),
                list_price=Money.brl(row["list_price_brl"]) if row["list_price_brl"] else None,
                captured_at=datetime.fromisoformat(row["captured_at"]),
                seller=row["seller"],
                is_prime=bool(row["is_prime"]),
            )
            for row in rows
        ]

    def close(self) -> None:
        """Fecha a conexão com o SQLite."""
        self._conn.close()
