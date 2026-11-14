from datetime import UTC, datetime
from pathlib import Path

from vinyl_scraper.domain.value_objects import Money
from vinyl_scraper.infrastructure.scrapers.amazon_br_parser import AmazonBrSearchParser


def test_parser_extracts_multiple_editions_and_brazilian_prices() -> None:
    html = Path("tests/fixtures/amazon_br_thriller_search.html").read_text(encoding="utf-8")
    parser = AmazonBrSearchParser()
    now = datetime(2026, 11, 14, 12, 0, tzinfo=UTC)

    editions = parser.parse_search_results(html, captured_at=now)

    assert len(editions) == 2

    ed1 = editions[0]
    assert ed1.asin.value == "B0B6X9V40A"
    assert "40th Anniversary" in ed1.title
    assert ed1.current_price == Money.brl("219.90")
    assert ed1.list_price == Money.brl("349.90")
    assert ed1.is_prime is True
    assert ed1.rating == 4.9
    assert ed1.review_count == 1245
    assert ed1.url == "https://www.amazon.com.br/dp/B0B6X9V40A"

    ed2 = editions[1]
    assert ed2.asin.value == "B000V9K8T2"
    assert ed2.current_price == Money.brl("1099.50")
    assert ed2.list_price is None
    assert ed2.is_prime is False
    assert ed2.review_count == 320


def test_parser_detects_captcha_page() -> None:
    parser = AmazonBrSearchParser()
    captcha_html = """
    <html><body>
      <form action="/errors/validateCaptcha">
        <h4>Digite os caracteres que você vê abaixo</h4>
      </form>
    </body></html>
    """
    assert parser.is_captcha_page(captcha_html) is True
    assert parser.is_captcha_page("<html><body>Normal page</body></html>") is False
