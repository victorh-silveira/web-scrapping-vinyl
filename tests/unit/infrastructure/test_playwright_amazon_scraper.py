from unittest.mock import MagicMock

import pytest

from vinyl_scraper.domain.entities import VinylQuery
from vinyl_scraper.domain.exceptions import ScraperBlockedError
from vinyl_scraper.infrastructure.scrapers import playwright_amazon_scraper as scraper_mod
from vinyl_scraper.infrastructure.scrapers.playwright_amazon_scraper import PlaywrightAmazonScraper


def _mock_playwright(monkeypatch: pytest.MonkeyPatch, html_pages: list[str]) -> None:
    page = MagicMock()
    page.content.side_effect = html_pages

    context = MagicMock()
    context.new_page.return_value = page

    browser = MagicMock()
    browser.new_context.return_value = context

    pw_instance = MagicMock()
    pw_instance.chromium.launch.return_value = browser

    cm = MagicMock()
    cm.__enter__.return_value = pw_instance
    cm.__exit__.return_value = False

    monkeypatch.setattr(scraper_mod, "sync_playwright", lambda: cm)
    monkeypatch.setattr(scraper_mod.time, "sleep", lambda _s: None)


def test_playwright_scraper_fetches_pages_and_stops_on_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page1_html = """
    <div data-asin="B0B6X9V40A" data-component-type="s-search-result">
      <h2><a href="/dp/B0B6X9V40A"><span>Thriller [Vinil]</span></a></h2>
      <span class="a-price"><span class="a-offscreen">R$ 219,90</span></span>
    </div>
    """
    _mock_playwright(monkeypatch, [page1_html, "<html></html>"])

    scraper = PlaywrightAmazonScraper(min_delay_sec=0.0, max_delay_sec=0.0)
    results = scraper.search_vinyl_editions(
        VinylQuery(artist="Michael Jackson", album="Thriller"), max_pages=2
    )

    assert len(results) == 1
    assert results[0].asin.value == "B0B6X9V40A"


def test_playwright_scraper_raises_on_captcha(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_playwright(monkeypatch, ['<form action="/errors/validateCaptcha"></form>'])

    scraper = PlaywrightAmazonScraper()
    with pytest.raises(ScraperBlockedError):
        scraper.search_vinyl_editions(
            VinylQuery(artist="Michael Jackson", album="Thriller"), max_pages=1
        )
