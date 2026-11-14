import json
from datetime import datetime
from pathlib import Path

from vinyl_scraper.domain.entities import AlbumSearchReport, VinylEdition, VinylQuery
from vinyl_scraper.domain.value_objects import (
    ASIN,
    BlackFridayComparison,
    CostBenefitScore,
    EditionInfo,
    Money,
    PriceStats,
)
from vinyl_scraper.infrastructure.io.json_catalog_reader import JsonCatalogReader
from vinyl_scraper.infrastructure.io.json_report_exporter import JsonReportExporter


def test_json_catalog_reader_loads_example_file() -> None:
    reader = JsonCatalogReader("data/vinyls.example.json")
    window, queries = reader.load()

    assert window.pre_bf_days == 30
    assert len(queries) == 2
    assert queries[0].artist == "Michael Jackson"
    assert queries[0].album == "Thriller"
    assert queries[0].max_price_brl == Money.brl("350.00")


def test_json_report_exporter_writes_ranked_summary(tmp_path: Path) -> None:
    out_file = tmp_path / "report.json"
    exporter = JsonReportExporter(out_file)
    query = VinylQuery(artist="Michael Jackson", album="Thriller")
    window, _ = JsonCatalogReader("data/vinyls.example.json").load()

    ed = VinylEdition(
        asin=ASIN("B0B6X9V40A"),
        title="Michael Jackson - Thriller 40th Anniversary [Vinil 180g]",
        url="https://www.amazon.com.br/dp/B0B6X9V40A",
        edition_info=EditionInfo(
            is_vinyl=True,
            edition_label="40th Anniversary / 180g",
            is_180g=True,
            is_anniversary=True,
        ),
        current_price=Money.brl("219.90"),
        list_price=Money.brl("349.90"),
        is_prime=True,
        rating=4.9,
        review_count=1245,
        seller="Amazon.com.br",
        stats=PriceStats(
            min_price=Money.brl("219.90"),
            max_price=Money.brl("349.90"),
            mean_price=Money.brl("284.90"),
            median_price=Money.brl("284.90"),
            sample_count=2,
        ),
        bf_comparison=BlackFridayComparison(
            pre_bf_mean_price=Money.brl("349.90"),
            pre_bf_last_price=Money.brl("349.90"),
            bf_price=Money.brl("219.90"),
            discount_vs_pre_bf_pct=Money.brl("219.90").discount_percentage_from(
                Money.brl("349.90")
            ),
            discount_vs_median_pct=Money.brl("219.90").discount_percentage_from(
                Money.brl("284.90")
            ),
            is_real_deal=True,
            deal_verdict="Excelente promoção real",
        ),
        cost_benefit=CostBenefitScore(
            total_score=82.5,
            discount_score=24.0,
            median_score=20.0,
            edition_score=24.0,
            trust_score=14.5,
        ),
    )

    path = exporter.export([AlbumSearchReport(query=query, editions=[ed])], window)
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    assert data["summary"]["albums_queried"] == 1
    assert data["summary"]["total_editions_found"] == 1
    assert len(data["summary"]["top_cost_benefit"]) == 1
    assert len(data["summary"]["top_promotions"]) == 1
    assert data["albums"][0]["editions"][0]["asin"] == "B0B6X9V40A"
    assert isinstance(datetime.fromisoformat(data["generated_at"]), datetime)
