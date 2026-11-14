"""Domain Service: PriceAnalyticsService for statistics, Black Friday, and cost-benefit."""

from __future__ import annotations

from decimal import Decimal
from statistics import mean, median

from vinyl_scraper.domain.edition_classifier import normalize_text
from vinyl_scraper.domain.entities import VinylQuery
from vinyl_scraper.domain.value_objects import (
    BlackFridayComparison,
    BlackFridayWindow,
    CostBenefitScore,
    EditionInfo,
    Money,
    PriceSnapshot,
    PriceStats,
    PriceWindowTag,
)


class PriceAnalyticsService:
    """Computes historical price statistics, Black Friday comparisons, and cost-benefit."""

    def compute_stats(self, snapshots: list[PriceSnapshot]) -> PriceStats:
        """Compute min, max, mean, and median over price snapshots."""
        if not snapshots:
            zero = Money.brl("0.00")
            return PriceStats(
                min_price=zero,
                max_price=zero,
                mean_price=zero,
                median_price=zero,
                sample_count=0,
            )

        amounts = [s.price.amount for s in snapshots]
        return PriceStats(
            min_price=Money.brl(min(amounts)),
            max_price=Money.brl(max(amounts)),
            mean_price=Money.brl(mean(amounts)),
            median_price=Money.brl(median(amounts)),
            sample_count=len(amounts),
        )

    def compare_black_friday(
        self,
        snapshots: list[PriceSnapshot],
        current_price: Money,
        list_price: Money | None,
        stats: PriceStats,
        window: BlackFridayWindow,
    ) -> BlackFridayComparison:
        """Compare Pre-Black Friday prices against Black Friday / current price."""
        latest_day = max((s.captured_at.date() for s in snapshots), default=None)
        pre_bf_snaps = [
            s
            for s in snapshots
            if window.classify(s.captured_at) == PriceWindowTag.PRE_BLACK_FRIDAY
        ]
        bf_snaps = [
            s for s in snapshots if window.classify(s.captured_at) == PriceWindowTag.BLACK_FRIDAY
        ]
        # On first run (all snapshots from a single day in pre-BF), treat Amazon's
        # strikethrough list_price as the prior reference instead of today's price.
        has_prior_day_pre_bf = any(
            latest_day is None or s.captured_at.date() < latest_day for s in pre_bf_snaps
        )

        pre_bf_mean: Money | None = None
        pre_bf_last: Money | None = None
        if pre_bf_snaps and (has_prior_day_pre_bf or bool(bf_snaps)):
            pre_bf_sorted = sorted(pre_bf_snaps, key=lambda s: s.captured_at)
            pre_bf_mean = Money.brl(mean(s.price.amount for s in pre_bf_sorted))
            pre_bf_last = pre_bf_sorted[-1].price
        elif list_price is not None and list_price > current_price:
            pre_bf_mean = list_price
            pre_bf_last = list_price
        elif pre_bf_snaps:
            pre_bf_sorted = sorted(pre_bf_snaps, key=lambda s: s.captured_at)
            pre_bf_mean = Money.brl(mean(s.price.amount for s in pre_bf_sorted))
            pre_bf_last = pre_bf_sorted[-1].price

        bf_price: Money | None = (
            min((s.price for s in bf_snaps), default=current_price) if bf_snaps else current_price
        )

        reference_pre_bf = pre_bf_last or pre_bf_mean
        discount_vs_pre_bf = (
            current_price.discount_percentage_from(reference_pre_bf)
            if reference_pre_bf is not None
            else Decimal("0.00")
        )
        discount_vs_median = (
            current_price.discount_percentage_from(stats.median_price)
            if stats.sample_count > 0
            else Decimal("0.00")
        )

        is_real_deal, verdict = self._evaluate_deal(
            current_price=current_price,
            list_price=list_price,
            pre_bf_mean=pre_bf_mean,
            discount_vs_pre_bf=discount_vs_pre_bf,
            discount_vs_median=discount_vs_median,
            sample_count=stats.sample_count,
        )

        return BlackFridayComparison(
            pre_bf_mean_price=pre_bf_mean,
            pre_bf_last_price=pre_bf_last,
            bf_price=bf_price,
            discount_vs_pre_bf_pct=discount_vs_pre_bf,
            discount_vs_median_pct=discount_vs_median,
            is_real_deal=is_real_deal,
            deal_verdict=verdict,
        )

    def compute_cost_benefit(
        self,
        query: VinylQuery,
        current_price: Money,
        stats: PriceStats,
        bf_comparison: BlackFridayComparison,
        edition_info: EditionInfo,
        is_prime: bool,
        rating: float | None,
        review_count: int,
    ) -> CostBenefitScore:
        """Compute a 0..100 cost-benefit score balancing discount, median, edition, and trust."""
        pre_bf_pct = max(Decimal("0"), min(Decimal("60"), bf_comparison.discount_vs_pre_bf_pct))
        discount_score = float(pre_bf_pct / Decimal("60")) * 30.0

        median_pct = max(Decimal("0"), min(Decimal("50"), bf_comparison.discount_vs_median_pct))
        median_score = float(median_pct / Decimal("50")) * 30.0

        if stats.sample_count > 1 and current_price <= stats.min_price:
            median_score = min(30.0, median_score + 5.0)

        edition_score = 5.0
        if edition_info.is_180g:
            edition_score += 5.0
        if edition_info.is_double_lp:
            edition_score += 4.0
        if edition_info.is_anniversary:
            edition_score += 4.0
        if edition_info.is_remastered:
            edition_score += 2.0
        if query.preferred_editions:
            norm_label = normalize_text(edition_info.edition_label)
            if any(normalize_text(pref) in norm_label for pref in query.preferred_editions):
                edition_score += 5.0
        edition_score = min(25.0, edition_score)

        trust_score = 0.0
        if is_prime:
            trust_score += 7.0
        if rating is not None:
            trust_score += min(5.0, max(0.0, (rating - 3.0) * 2.5))
        if review_count >= 50:
            trust_score += 3.0
        elif review_count >= 10:
            trust_score += 1.5
        trust_score = min(15.0, trust_score)

        total = discount_score + median_score + edition_score + trust_score

        if query.max_price_brl is not None and current_price > query.max_price_brl:
            total *= 0.65

        return CostBenefitScore(
            total_score=round(min(100.0, max(0.0, total)), 2),
            discount_score=round(discount_score, 2),
            median_score=round(median_score, 2),
            edition_score=round(edition_score, 2),
            trust_score=round(trust_score, 2),
        )

    def _evaluate_deal(
        self,
        current_price: Money,
        list_price: Money | None,
        pre_bf_mean: Money | None,
        discount_vs_pre_bf: Decimal,
        discount_vs_median: Decimal,
        sample_count: int,
    ) -> tuple[bool, str]:
        if (
            pre_bf_mean is not None
            and current_price > pre_bf_mean
            and list_price is not None
            and list_price > current_price
            and discount_vs_pre_bf < Decimal("0")
        ):
            return False, "Falso desconto (acima da média pré-Black Friday)"

        if discount_vs_pre_bf >= Decimal("15.00") or discount_vs_median >= Decimal("15.00"):
            return True, "Excelente promoção real"
        if discount_vs_pre_bf >= Decimal("5.00") or discount_vs_median >= Decimal("5.00"):
            return True, "Boa oferta"
        if sample_count <= 1 and list_price is None:
            return False, "Primeiro registro (sem histórico suficiente)"
        return False, "Preço dentro da média histórica"
