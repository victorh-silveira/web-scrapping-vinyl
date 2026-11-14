import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from vinyl_scraper.domain.entities import ScrapedEdition, VinylQuery
from vinyl_scraper.domain.exceptions import ScraperBlockedError
from vinyl_scraper.domain.value_objects import ASIN, Money
from vinyl_scraper.presentation import cli as cli_mod


def test_cli_run_and_analyze_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_file = tmp_path / "vinyls.json"
    input_file.write_text(
        json.dumps(
            {
                "black_friday_window": {
                    "start": "2026-11-20",
                    "end": "2026-11-30",
                    "pre_bf_days": 30,
                },
                "vinyls": [
                    {"artist": "Michael Jackson", "album": "Thriller"},
                    {"artist": "Pink Floyd", "album": "Wish You Were Here"},
                ],
            }
        ),
        encoding="utf-8",
    )
    output_file = tmp_path / "report.json"
    db_file = tmp_path / "history.db"

    class FakeScraper:
        def __init__(self, headless: bool = True) -> None:
            self.headless = headless

        def search_vinyl_editions(
            self, query: VinylQuery, max_pages: int = 2
        ) -> list[ScrapedEdition]:
            if query.album == "Wish You Were Here":
                raise ScraperBlockedError(query.search_term, "CAPTCHA")
            return [
                ScrapedEdition(
                    asin=ASIN("B0B6X9V40A"),
                    title="Michael Jackson - Thriller [Vinil 180g]",
                    url="https://www.amazon.com.br/dp/B0B6X9V40A",
                    current_price=Money.brl("219.90"),
                    list_price=Money.brl("320.00"),
                    captured_at=datetime(2026, 11, 25, 12, 0, tzinfo=UTC),
                    is_prime=True,
                )
            ]

    monkeypatch.setattr(cli_mod, "PlaywrightAmazonScraper", FakeScraper)
    runner = CliRunner()

    run_res = runner.invoke(
        cli_mod.app,
        [
            "run",
            "--input",
            str(input_file),
            "--output",
            str(output_file),
            "--db",
            str(db_file),
            "--bf-start",
            "2026-11-20",
        ],
    )
    assert run_res.exit_code == 0
    assert output_file.exists()

    analyze_res = runner.invoke(
        cli_mod.app,
        [
            "analyze",
            "--input",
            str(input_file),
            "--output",
            str(output_file),
            "--db",
            str(db_file),
        ],
    )
    assert analyze_res.exit_code == 0
