"""
Tests for parse_ggi_list.

DEFERRED — robots.txt blocks the entire ggi.co.kr site (Disallow: /):
  - /search/besttop_list.asp (조회수 TOP50 page, JS-rendered via AJAX)
  - /search/besttop_query.asp (AJAX data endpoint returning HTML fragment)

No production fixture exists because fetching from Disallowed paths is prohibited.
The parser is a stub returning []. Tests are marked xfail(strict=True) so that
the suite stays green until robots.txt policy changes or official access is
negotiated.

Real values observed during development recon on 2026-07-03
(GET /search/besttop_query.asp — top-50 results):
  Rank 1: court="여주2계",  ggi_case="2023-2003",    standard="2023타경2003",    views=3085
  Rank 2: court="중앙7계",  ggi_case="2024-114251",  standard="2024타경114251",  views=2471
  Rank 3: court="동부3계",  ggi_case="2023-60336[1]", standard="2023타경60336(1)", views=2437

See tests/fixtures/ggi/NOTES.md for full details.

To un-defer this task:
  1. Confirm /search/ or an alternative path is allowed in robots.txt.
  2. Save a real fixture (list.html from GET /search/besttop_query.asp).
  3. Implement parse_ggi_list in src/auction_tracker/sources/parse/ggi.py.
  4. Remove the @pytest.mark.xfail decorators below.
"""

from pathlib import Path

import pytest

from auction_tracker.sources.parse.ggi import parse_ggi_list
from auction_tracker.sources.types import SourceName

# Fixture path (does not exist yet — fetching Disallowed by robots.txt)
FIXTURE = Path(__file__).parent.parent / "fixtures" / "ggi" / "list.html"

# Real values from development recon 2026-07-03
EXPECTED_CASE_NO = "2023타경2003"   # ggi "2023-2003" normalised to standard format
EXPECTED_VIEWS = 3085               # viewed as integer (3,085 with comma stripped)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "ggi.co.kr is Disallow:/ in robots.txt; no fixture saved; "
        "parse_ggi_list is a stub returning []. "
        "See tests/fixtures/ggi/NOTES.md."
    ),
)
def test_parse_ggi_list_extracts_rows():
    rows = parse_ggi_list(FIXTURE.read_text(encoding="utf-8"))
    assert len(rows) >= 1
    by_case = {c: r for c, r in rows}
    assert EXPECTED_CASE_NO in by_case, (
        f"Expected case {EXPECTED_CASE_NO!r} not found in {list(by_case.keys())[:5]}"
    )
    assert by_case[EXPECTED_CASE_NO].source is SourceName.GGI
    assert by_case[EXPECTED_CASE_NO].view_count == EXPECTED_VIEWS


@pytest.mark.xfail(
    strict=True,
    reason=(
        "ggi.co.kr is Disallow:/ in robots.txt; parse_ggi_list is a stub. "
        "See tests/fixtures/ggi/NOTES.md."
    ),
)
def test_parse_ggi_list_returns_fifty_rows():
    """The default besttop_query.asp call returns 50 items (TOP50)."""
    rows = parse_ggi_list(FIXTURE.read_text(encoding="utf-8"))
    assert len(rows) == 50


@pytest.mark.xfail(
    strict=True,
    reason=(
        "ggi.co.kr is Disallow:/ in robots.txt; parse_ggi_list is a stub. "
        "See tests/fixtures/ggi/NOTES.md."
    ),
)
def test_parse_ggi_list_all_sources_are_ggi():
    rows = parse_ggi_list(FIXTURE.read_text(encoding="utf-8"))
    for case_no, result in rows:
        assert result.source is SourceName.GGI, f"{case_no} has wrong source"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "ggi.co.kr is Disallow:/ in robots.txt; parse_ggi_list is a stub. "
        "See tests/fixtures/ggi/NOTES.md."
    ),
)
def test_parse_ggi_list_view_counts_are_ints():
    rows = parse_ggi_list(FIXTURE.read_text(encoding="utf-8"))
    for case_no, result in rows:
        assert isinstance(result.view_count, int), (
            f"{case_no}: expected int view_count, got {type(result.view_count)}"
        )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "ggi.co.kr is Disallow:/ in robots.txt; parse_ggi_list is a stub. "
        "See tests/fixtures/ggi/NOTES.md."
    ),
)
def test_parse_ggi_list_case_no_format():
    """Case numbers must be in standard YYYY타경NNNN format (no hyphens, no [N] suffix)."""
    rows = parse_ggi_list(FIXTURE.read_text(encoding="utf-8"))
    import re
    standard_pattern = re.compile(r"^\d{4}타경\d+(\(\d+\))?$")
    for case_no, _ in rows:
        assert standard_pattern.match(case_no), (
            f"Case number {case_no!r} does not match standard YYYY타경NNNN format"
        )


def test_parse_ggi_list_handles_empty_html():
    """Stub always returns [] — empty input should also return []."""
    assert parse_ggi_list("") == []


def test_parse_ggi_list_handles_invalid_input():
    """Stub always returns [] regardless of input."""
    assert parse_ggi_list("<html>no data here</html>") == []
