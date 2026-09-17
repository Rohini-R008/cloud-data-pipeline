from src.clean import normalize_country


def test_aliases_map_to_canonical():
    assert normalize_country("USA") == "United States"
    assert normalize_country("United States of America") == "United States"
    assert normalize_country("united states") == "United States"


def test_unknown_country_is_titlecased():
    assert normalize_country("japan") == "Japan"


def test_whitespace_is_stripped_and_collapsed():
    assert normalize_country("  France  ") == "France"
    assert normalize_country(" united   kingdom ") == "United Kingdom"