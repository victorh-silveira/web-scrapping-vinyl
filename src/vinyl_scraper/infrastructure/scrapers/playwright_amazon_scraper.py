"""Adaptador de scraper da Amazon BR baseado em Playwright."""

from __future__ import annotations

import random
import time
from datetime import UTC, datetime
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright

from vinyl_scraper.domain.entities import ScrapedEdition, VinylQuery
from vinyl_scraper.domain.exceptions import ScraperBlockedError
from vinyl_scraper.infrastructure.scrapers.amazon_br_parser import AmazonBrSearchParser


class PlaywrightAmazonScraper:
    """Coleta buscas da Amazon BR usando Playwright Chromium com atrasos respeitosos."""

    def __init__(
        self,
        headless: bool = True,
        min_delay_sec: float = 2.0,
        max_delay_sec: float = 4.5,
        parser: AmazonBrSearchParser | None = None,
    ) -> None:
        self._headless = headless
        self._min_delay_sec = min_delay_sec
        self._max_delay_sec = max_delay_sec
        self._parser = parser or AmazonBrSearchParser()

    def search_vinyl_editions(self, query: VinylQuery, max_pages: int = 2) -> list[ScrapedEdition]:
        """Busca até `max_pages` páginas de resultados na Amazon BR para `query`."""
        all_editions: list[ScrapedEdition] = []
        encoded_q = quote_plus(query.search_term)

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self._headless)
            context = browser.new_context(
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
                viewport={"width": 1366, "height": 768},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()

            try:
                for page_num in range(1, max_pages + 1):
                    url = f"https://www.amazon.com.br/s?k={encoded_q}&i=popular&page={page_num}"
                    page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                    # Wait briefly for dynamic price slots
                    page.wait_for_timeout(1200)
                    html = page.content()

                    if self._parser.is_captcha_page(html):
                        raise ScraperBlockedError(
                            query.search_term,
                            f"Amazon BR apresentou CAPTCHA na página {page_num}.",
                        )

                    parsed = self._parser.parse_search_results(html, captured_at=datetime.now(UTC))
                    if not parsed:
                        break
                    all_editions.extend(parsed)

                    if page_num < max_pages:
                        time.sleep(random.uniform(self._min_delay_sec, self._max_delay_sec))
            finally:
                context.close()
                browser.close()

        return all_editions
