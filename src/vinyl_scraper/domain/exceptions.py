"""Domain exceptions for the vinyl scraper."""


class DomainError(Exception):
    """Base exception for domain rule violations."""


class InvalidMoneyError(DomainError):
    """Raised when a monetary value is invalid or negative."""


class InvalidAsinError(DomainError):
    """Raised when an Amazon ASIN fails validation."""


class ScraperBlockedError(DomainError):
    """Raised when Amazon BR presents a CAPTCHA or anti-bot block."""

    def __init__(self, query_label: str, reason: str = "CAPTCHA or anti-bot block") -> None:
        self.query_label = query_label
        self.reason = reason
        super().__init__(f"Scraping blocked for '{query_label}': {reason}")
