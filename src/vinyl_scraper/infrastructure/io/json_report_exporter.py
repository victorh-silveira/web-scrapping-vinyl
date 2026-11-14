"""JSON report exporter adapter."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from vinyl_scraper.domain.entities import AlbumSearchReport, VinylEdition
from vinyl_scraper.domain.value_objects import BlackFridayWindow


def _serialize_edition(ed: VinylEdition, artist: str, album: str) -> dict[str, Any]:
    return {
        "asin": ed.asin.value,
        "artist": artist,
        "album": album,
        "title": ed.title,
        "edition_label": ed.edition_info.edition_label,
        "attributes": {
            "is_180g": ed.edition_info.is_180g,
            "is_double_lp": ed.edition_info.is_double_lp,
            "is_picture_disc": ed.edition_info.is_picture_disc,
            "is_colored": ed.edition_info.is_colored,
            "is_anniversary": ed.edition_info.is_anniversary,
            "is_import": ed.edition_info.is_import,
            "is_remastered": ed.edition_info.is_remastered,
        },
        "url": ed.url,
        "current_price_brl": float(ed.current_price.amount),
        "list_price_brl": float(ed.list_price.amount) if ed.list_price else None,
        "is_prime": ed.is_prime,
        "rating": ed.rating,
        "review_count": ed.review_count,
        "seller": ed.seller,
        "price_history_stats": {
            "min_brl": float(ed.stats.min_price.amount),
            "max_brl": float(ed.stats.max_price.amount),
            "mean_brl": float(ed.stats.mean_price.amount),
            "median_brl": float(ed.stats.median_price.amount),
            "sample_count": ed.stats.sample_count,
        },
        "black_friday_comparison": {
            "pre_bf_mean_brl": (
                float(ed.bf_comparison.pre_bf_mean_price.amount)
                if ed.bf_comparison.pre_bf_mean_price
                else None
            ),
            "pre_bf_last_brl": (
                float(ed.bf_comparison.pre_bf_last_price.amount)
                if ed.bf_comparison.pre_bf_last_price
                else None
            ),
            "bf_price_brl": (
                float(ed.bf_comparison.bf_price.amount) if ed.bf_comparison.bf_price else None
            ),
            "discount_vs_pre_bf_pct": float(ed.bf_comparison.discount_vs_pre_bf_pct),
            "discount_vs_median_pct": float(ed.bf_comparison.discount_vs_median_pct),
            "is_real_deal": ed.bf_comparison.is_real_deal,
            "deal_verdict": ed.bf_comparison.deal_verdict,
        },
        "cost_benefit": {
            "total_score": ed.cost_benefit.total_score,
            "discount_score": ed.cost_benefit.discount_score,
            "median_score": ed.cost_benefit.median_score,
            "edition_score": ed.cost_benefit.edition_score,
            "trust_score": ed.cost_benefit.trust_score,
        },
    }


class JsonReportExporter:
    """Exports analyzed vinyl editions and top rankings to a structured JSON file."""

    def __init__(self, output_path: str | Path = "output/report.json") -> None:
        self._output_path = Path(output_path)

    def export(self, reports: list[AlbumSearchReport], window: BlackFridayWindow) -> str:
        """Write the full report to JSON and return the output file path."""
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        all_serialized: list[dict[str, Any]] = []
        albums_payload: list[dict[str, Any]] = []
        blocked_queries: list[dict[str, str]] = []

        for report in reports:
            if report.blocked:
                blocked_queries.append(
                    {
                        "artist": report.query.artist,
                        "album": report.query.album,
                        "reason": report.error_message or "Blocked",
                    }
                )
            editions_json = [
                _serialize_edition(ed, report.query.artist, report.query.album)
                for ed in report.editions
            ]
            all_serialized.extend(editions_json)
            albums_payload.append(
                {
                    "artist": report.query.artist,
                    "album": report.query.album,
                    "editions_found": len(editions_json),
                    "blocked": report.blocked,
                    "error_message": report.error_message,
                    "editions": editions_json,
                }
            )

        top_cost_benefit = sorted(
            all_serialized,
            key=lambda x: x["cost_benefit"]["total_score"],
            reverse=True,
        )[:10]

        top_promotions = sorted(
            [e for e in all_serialized if e["black_friday_comparison"]["is_real_deal"]],
            key=lambda x: (
                x["black_friday_comparison"]["discount_vs_median_pct"],
                x["black_friday_comparison"]["discount_vs_pre_bf_pct"],
            ),
            reverse=True,
        )[:10]

        payload = {
            "generated_at": datetime.now(UTC).isoformat(),
            "black_friday_window": {
                "start": window.start.isoformat(),
                "end": window.end.isoformat(),
                "pre_bf_days": window.pre_bf_days,
            },
            "summary": {
                "albums_queried": len(reports),
                "total_editions_found": len(all_serialized),
                "blocked_count": len(blocked_queries),
                "blocked_queries": blocked_queries,
                "top_cost_benefit": top_cost_benefit,
                "top_promotions": top_promotions,
            },
            "albums": albums_payload,
        }

        self._output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return str(self._output_path)
