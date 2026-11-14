from vinyl_scraper.domain.entities import VinylQuery
from vinyl_scraper.domain.services import EditionClassifier


def test_classifier_accepts_multiple_thriller_vinyl_editions() -> None:
    classifier = EditionClassifier()
    query = VinylQuery(artist="Michael Jackson", album="Thriller")

    ed_standard = classifier.classify("Michael Jackson - Thriller [Disco de Vinil]", query)
    ed_25 = classifier.classify(
        "Thriller 25th Anniversary Edition (2LP 180g Importado) Vinil", query
    )
    ed_40 = classifier.classify(
        "Michael Jackson: Thriller 40th Anniversary [Vinyl LP Remastered]", query
    )
    ed_picture = classifier.classify(
        "Thriller (Picture Disc) - Michael Jackson [Vinil Colorido]", query
    )

    assert ed_standard.is_vinyl is True
    assert ed_25.is_vinyl is True
    assert ed_25.is_anniversary is True
    assert ed_25.is_180g is True
    assert ed_25.is_double_lp is True
    assert ed_25.is_import is True
    assert "25th Anniversary" in ed_25.edition_label

    assert ed_40.is_vinyl is True
    assert ed_40.is_remastered is True
    assert "40th Anniversary" in ed_40.edition_label

    assert ed_picture.is_vinyl is True
    assert ed_picture.is_picture_disc is True
    assert ed_picture.is_colored is True


def test_classifier_rejects_non_vinyl_items() -> None:
    classifier = EditionClassifier()
    query = VinylQuery(artist="Michael Jackson", album="Thriller")

    cd = classifier.classify("Michael Jackson - Thriller (CD Álbum)", query)
    shirt = classifier.classify("Camiseta Michael Jackson Thriller Preta", query)
    book = classifier.classify("Livro: Making of Thriller - Michael Jackson", query)
    mp3 = classifier.classify("Thriller [MP3 Download]", query)

    assert cd.is_vinyl is False
    assert shirt.is_vinyl is False
    assert book.is_vinyl is False
    assert mp3.is_vinyl is False


def test_classifier_rejects_unrelated_album() -> None:
    classifier = EditionClassifier()
    query = VinylQuery(artist="Michael Jackson", album="Thriller")

    other = classifier.classify("Michael Jackson - Bad [Disco de Vinil 180g]", query)
    assert other.is_vinyl is False


def test_classifier_matches_soundtrack_ost_without_literal_ost() -> None:
    classifier = EditionClassifier()
    query = VinylQuery(artist="Various Artists", album="Dirty Dancing OST")
    ed = classifier.classify("Dirty Dancing - Trilha Sonora Original [Disco de Vinil]", query)
    assert ed.is_vinyl is True
