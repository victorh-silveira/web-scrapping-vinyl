"""Serviço de Domínio: EditionClassifier para filtrar não-vinis e extrair dados de edição."""

from __future__ import annotations

import re
import unicodedata

from vinyl_scraper.domain.entities import VinylQuery
from vinyl_scraper.domain.value_objects import EditionInfo

_VINYL_POSITIVE_KEYWORDS = (
    "vinil",
    "vinyl",
    "disco de vinil",
    "lp",
    "2lp",
    "3lp",
    "180g",
    "180 g",
    "picture disc",
    "gatefold",
)

_NON_VINYL_NEGATIVE_KEYWORDS = (
    "camiseta",
    "camisa",
    "caneca",
    "poster",
    "quadro",
    "livro",
    "book",
    "vitrola",
    "toca-discos",
    "toca discos",
    "agulha",
    "mp3",
    "streaming",
    "dvd",
    "blu-ray",
    "bluray",
    "funko",
    "chaveiro",
    "boneco",
    "cd de audio",
    "audio cd",
    "cd ",
    "(cd)",
    "[cd]",
    "cd album",
)

_TRIBUTE_KEYWORDS = ("tribute to", "metal tribute", "tributo a", "karaoke")
_FALSE_HOMONYM_KEYWORDS = ("pops", "hardcore", "philharmonic", "symphony")

_ANNIVERSARY_PATTERN = re.compile(r"\b(\d{1,2})(th|st|nd|rd)\s+anniversary\b", re.IGNORECASE)


def normalize_text(text: str) -> str:
    """Converte para minúsculas e remove diacríticos para comparação sem acentos."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


class EditionClassifier:
    """Classifica títulos da Amazon BR para filtrar não-vinis e extrair atributos da edição."""

    def classify(
        self, title: str, query: VinylQuery, format_hint: str | None = None
    ) -> EditionInfo:
        """Determina se `title` é uma edição em vinil correspondente e extrai seus atributos."""
        norm = normalize_text(title)
        norm_hint = normalize_text(format_hint) if format_hint else ""
        combined = f"{norm} {norm_hint}".strip()

        if not self._matches_query(norm, query):
            return EditionInfo(is_vinyl=False, edition_label="Mismatch")

        if any(bad in combined for bad in _NON_VINYL_NEGATIVE_KEYWORDS):
            return EditionInfo(is_vinyl=False, edition_label="Non-Vinyl")

        query_norm = normalize_text(f"{query.artist} {query.album}")
        if (
            "tribute" not in query_norm
            and "tributo" not in query_norm
            and any(trib in norm for trib in _TRIBUTE_KEYWORDS)
        ):
            return EditionInfo(is_vinyl=False, edition_label="Tribute")

        has_vinyl_marker = any(kw in combined for kw in _VINYL_POSITIVE_KEYWORDS)
        if not has_vinyl_marker:
            return EditionInfo(is_vinyl=False, edition_label="Unknown Format")

        is_180g = "180g" in norm or "180 g" in norm or "180 gram" in norm
        is_double_lp = any(tok in norm for tok in ("2lp", "2 lp", "double lp", "duplo"))
        is_picture_disc = "picture disc" in norm or "picturedisc" in norm
        is_colored = any(
            tok in norm for tok in ("colorido", "colored", "coloured", "translucent", "splatter")
        )
        is_import = any(tok in norm for tok in ("importado", "import", "eua", "uk", "eu"))
        is_remastered = "remaster" in norm

        ann_match = _ANNIVERSARY_PATTERN.search(title)
        is_anniversary = ann_match is not None or "anniversary" in norm or "aniversario" in norm

        tags: list[str] = []
        if ann_match:
            tags.append(f"{ann_match.group(1)}{ann_match.group(2).lower()} Anniversary")
        elif is_anniversary:
            tags.append("Anniversary Edition")
        if is_picture_disc:
            tags.append("Picture Disc")
        if is_colored:
            tags.append("Colored")
        if is_double_lp:
            tags.append("2LP")
        if is_180g:
            tags.append("180g")
        if is_remastered:
            tags.append("Remastered")
        if is_import:
            tags.append("Importado")

        label = " / ".join(tags) if tags else "Standard LP"
        return EditionInfo(
            is_vinyl=True,
            edition_label=label,
            is_180g=is_180g,
            is_double_lp=is_double_lp,
            is_picture_disc=is_picture_disc,
            is_colored=is_colored,
            is_anniversary=is_anniversary,
            is_import=is_import,
            is_remastered=is_remastered,
        )

    def _matches_query(self, normalized_title: str, query: VinylQuery) -> bool:
        candidates = (query.album, *query.aliases)
        artist_tokens = [
            t
            for t in normalize_text(query.artist).split()
            if len(t) > 2 and t not in {"various", "artists"}
        ]
        for candidate in candidates:
            album_tokens = [
                t for t in normalize_text(candidate).split() if len(t) > 2 and t != "ost"
            ]
            album_ok = (
                all(tok in normalized_title for tok in album_tokens) if album_tokens else True
            )
            if not album_ok:
                continue
            if (
                len(album_tokens) <= 1
                and len(normalize_text(candidate).strip()) < 6
                and artist_tokens
                and not any(tok in normalized_title for tok in artist_tokens)
            ):
                continue
            if len(album_tokens) == 1 and any(
                bad in normalized_title for bad in _FALSE_HOMONYM_KEYWORDS
            ):
                continue
            return True
        return False
