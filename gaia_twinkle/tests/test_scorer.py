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


def test_score_no_false_positive_short_number_substring():
    # 短数字金标不得子串误匹配更长的数（修复 "17" in "17000" 假阳）
    assert score("17000", "17") is False
    assert score("13", "3") is False
    assert score("42", "4") is False


def test_score_single_token_whole_word_match():
    # 单 token 金标需整 token 命中（"17" 是 "17 books" 的 token → 对）
    assert score("17 books", "17") is True
    assert score("Paris, France", "Paris") is True  # "paris" 是 token


def test_score_multi_token_substring():
    # 多 token 金标（短语）仍用子串
    assert score("INT. THE CASTLE - DAY", "THE CASTLE") is True
