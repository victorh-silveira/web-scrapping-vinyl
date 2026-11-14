"""Exceções de domínio para o scraper de vinis."""


class DomainError(Exception):
    """Exceção base para violações de regras de domínio."""


class InvalidMoneyError(DomainError):
    """Lançada quando um valor monetário é inválido ou negativo."""


class InvalidAsinError(DomainError):
    """Lançada quando um ASIN da Amazon falha na validação."""


class ScraperBlockedError(DomainError):
    """Lançada quando a Amazon BR apresenta CAPTCHA ou bloqueio anti-bot."""

    def __init__(self, query_label: str, reason: str = "CAPTCHA or anti-bot block") -> None:
        self.query_label = query_label
        self.reason = reason
        super().__init__(f"Scraping blocked for '{query_label}': {reason}")
