from src.utils import format_number


def test_format_number_small():
    assert format_number(0) == "0"
    assert format_number(42) == "42"
    assert format_number(999.4) == "999"


def test_format_number_thousands():
    assert format_number(1234) == "1.234"
    assert format_number(99999) == "99.999"


def test_format_number_large_scales():
    assert format_number(1_500_000) == "1,50 Mio."
    assert format_number(2_400_000_000) == "2,40 Mrd."
    assert format_number(10_000_000_000_000) == "10,00 Bio."
