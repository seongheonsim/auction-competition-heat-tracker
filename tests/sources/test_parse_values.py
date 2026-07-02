import datetime as dt

from auction_tracker.sources.parse.values import parse_int, parse_kdate, parse_money


def test_parse_money():
    assert parse_money("552,000,000원") == 552000000
    assert parse_money(" 1,234 ") == 1234
    assert parse_money("") is None
    assert parse_money("-") is None


def test_parse_int():
    assert parse_int("유찰 2회") == 2
    assert parse_int("1,234") == 1234
    assert parse_int("없음") is None


def test_parse_kdate():
    assert parse_kdate("2026.07.02") == dt.date(2026, 7, 2)
    assert parse_kdate("2026-07-02") == dt.date(2026, 7, 2)
    assert parse_kdate("미정") is None
