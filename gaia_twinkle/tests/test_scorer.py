from gaia_twinkle.scorer import normalize, score


def test_normalize_lowercases():
    assert normalize("Paris") == "paris"


def test_normalize_strips_punctuation_and_articles():
    assert normalize("The Eiffel Tower!") == "eiffel tower"
    assert normalize("a cat") == "cat"


def test_normalize_thousands_and_decimal():
    assert normalize("1,000") == "1000"
    assert normalize("1.0") == "1"
    assert normalize("3.14") == "3.14"  # decimal preserved


def test_normalize_unicode_nfkc():
    assert normalize("Gabriel García Márquez") == "gabriel garcia marquez"


def test_score_exact_and_substring():
    assert score("Paris", "Paris") is True
    assert score("Paris, France", "Paris") is True  # substring
    assert score("London", "Paris") is False


def test_score_number_normalization():
    assert score("1,000", "1000") is True
    assert score("1.0", "1") is True


def test_score_empty_gold_only_matches_empty():
    assert score("", "") is True
    assert score("anything", "") is False
