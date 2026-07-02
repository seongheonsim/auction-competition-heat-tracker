"""
Tests for parse_tank_list.

FIXTURE NOTE: tankauction.com ca/caList.php is JS-rendered (tbody is empty in static
HTML). List data is served as JSON from /api/proxy/api1.php/ca/AuctList.php.
The fixture is therefore JSON, not HTML. See tests/fixtures/tank/NOTES.md for full
recon details and robots.txt assessment.

EXPECTED values are taken directly from tests/fixtures/tank/list.json (row 1):
  case "2020타경16401" → hit=147
"""

from pathlib import Path

from auction_tracker.sources.parse.tank import parse_tank_list
from auction_tracker.sources.types import SourceName

# Fixture is JSON (not HTML) because the list page is JS-rendered
FIXTURE = Path(__file__).parent.parent / "fixtures" / "tank" / "list.json"

# Real values read from tests/fixtures/tank/list.json row 1 (sn1=2020, sn2=16401, pn=0, hit=147)
EXPECTED_CASE_NO = "2020타경16401"
EXPECTED_VIEWS = 147


def test_parse_tank_list_extracts_rows():
    rows = parse_tank_list(FIXTURE.read_text(encoding="utf-8"))
    assert len(rows) >= 1
    by_case = {c: r for c, r in rows}
    assert EXPECTED_CASE_NO in by_case, (
        f"Expected case {EXPECTED_CASE_NO!r} not found in {list(by_case.keys())[:5]}"
    )
    assert by_case[EXPECTED_CASE_NO].source is SourceName.TANK
    assert by_case[EXPECTED_CASE_NO].view_count == EXPECTED_VIEWS


def test_parse_tank_list_returns_twenty_rows():
    """The default API page returns 20 items — fixture should have all 20."""
    rows = parse_tank_list(FIXTURE.read_text(encoding="utf-8"))
    assert len(rows) == 20


def test_parse_tank_list_all_sources_are_tank():
    rows = parse_tank_list(FIXTURE.read_text(encoding="utf-8"))
    for case_no, result in rows:
        assert result.source is SourceName.TANK, f"{case_no} has wrong source"


def test_parse_tank_list_view_counts_are_ints():
    rows = parse_tank_list(FIXTURE.read_text(encoding="utf-8"))
    for case_no, result in rows:
        assert isinstance(result.view_count, int), (
            f"{case_no}: expected int view_count, got {type(result.view_count)}"
        )


def test_parse_tank_list_handles_empty_json():
    assert parse_tank_list("{}") == []


def test_parse_tank_list_handles_invalid_json():
    assert parse_tank_list("not json") == []
