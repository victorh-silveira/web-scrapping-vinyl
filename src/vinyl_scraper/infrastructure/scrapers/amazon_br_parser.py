"""Pure HTML parser for Amazon BR search results."""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup, Tag

from vinyl_scraper.domain.entities import ScrapedEdition
from vinyl_scraper.domain.exceptions import InvalidAsinError, InvalidMoneyError
from vinyl_scraper.domain.value_objects import ASIN, Money

_PRICE_CLEAN_RE = re.compile(r"[^\d,.]")
_RATING_RE = re.compile(r"(\d+[.,]\d+)")
_INT_RE = re.compile(r"[^\d]")


def parse_brl_price(raw: str) -> Money | None:
    """Parse Brazilian Real strings such as 'R$ 1.299,90' into Money."""
    cleaned = _PRICE_CLEAN_RE.sub("", raw.strip())
    if not cleaned:
        return None
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return Money.brl(Decimal(cleaned))
    except (InvalidOperation, InvalidMoneyError):
        return None


class AmazonBrSearchParser:
    """Parses Amazon BR search result HTML pages into ScrapedEdition objects."""

    BASE_URL = "https://www.amazon.com.br"

    def is_captcha_page(self, html: str) -> bool:
        """Detect Amazon CAPTCHA or anti-bot verification pages."""
        lower = html.lower()
        markers = (
            "/errors/validatecaptcha",
            "digite os caracteres que você vê",
            "type the characters you see in this image",
            "opfcaptcha",
        )
        return any(marker in lower for marker in markers)

    def parse_search_results(self, html: str, captured_at: datetime) -> list[ScrapedEdition]:
        """Extract all valid product cards with prices from an Amazon BR search page."""
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select('div[data-component-type="s-search-result"][data-asin]')
        editions: list[ScrapedEdition] = []

        for card in cards:
            parsed = self._parse_card(card, captured_at)
            if parsed is not None:
                editions.append(parsed)

        return editions

    def _parse_card(self, card: Tag, captured_at: datetime) -> ScrapedEdition | None:
        raw_asin = str(card.get("data-asin", "")).strip()
        if not raw_asin:
            return None
        try:
            asin = ASIN(raw_asin)
        except InvalidAsinError:
            return None

        title_el = card.select_one("h2 a span") or card.select_one("h2 span")
        if title_el is None:
            return None
        title = title_el.get_text(" ", strip=True)
        if not title:
            return None

        link_el = card.select_one("h2 a")
        href = str(link_el.get("href", "")) if link_el else ""
        url = (
            f"{self.BASE_URL}{href.split('?')[0]}"
            if href.startswith("/")
            else f"{self.BASE_URL}/dp/{asin.value}"
        )

        # Current price: prefer non-strike a-price > span.a-offscreen.
        # Strikethrough "De:" price must explicitly have data-a-strike="true"
        # so installment prices ("em até 6x de R$ ...") are never mistaken for list_price.
        current_price: Money | None = None
        list_price: Money | None = None
        for price_span in card.select("span.a-price"):
            offscreen = price_span.select_one("span.a-offscreen")
            if offscreen is None:
                continue
            parsed_money = parse_brl_price(offscreen.get_text(strip=True))
            if parsed_money is None:
                continue
            is_strike = price_span.get("data-a-strike") == "true"
            if is_strike:
                if list_price is None:
                    list_price = parsed_money
            elif current_price is None and "a-text-price" not in (price_span.get("class") or []):
                current_price = parsed_money

        if current_price is None:
            return None

        if list_price is not None and list_price <= current_price:
            list_price = None

        format_hint = self._extract_format_hint(card)

        is_prime = card.select_one("i.a-icon-prime") is not None

        rating: float | None = None
        rating_el = card.select_one("span.a-icon-alt")
        if rating_el:
            match = _RATING_RE.search(rating_el.get_text(strip=True))
            if match:
                rating = float(match.group(1).replace(",", "."))

        review_count = 0
        review_el = card.select_one("span.a-size-base.s-underline-text")
        if review_el:
            digits = _INT_RE.sub("", review_el.get_text(strip=True))
            if digits:
                review_count = int(digits)

        return ScrapedEdition(
            asin=asin,
            title=title,
            url=url,
            current_price=current_price,
            list_price=list_price,
            captured_at=captured_at,
            is_prime=is_prime,
            rating=rating,
            review_count=review_count,
            seller="Amazon.com.br" if is_prime else None,
            format_hint=format_hint,
        )

    def _extract_format_hint(self, card: Tag) -> str | None:
        format_markers = (
            "disco de vinil",
            "vinil",
            "vinyl",
            "cd de áudio",
            "cd de audio",
            "audio cd",
            "mp3",
        )
        for el in card.select("a.a-size-base.a-link-normal, span.a-text-bold"):
            txt = el.get_text(" ", strip=True)
            lower = txt.lower()
            if any(marker in lower for marker in format_markers):
                return txt
        return None
