"""
Tests for parse_dooin_list.

DEFERRED — robots.txt blocks /ca/ (Disallow:/ca/):
  - /ca/caTopView.php (view-count ranking page, JS-rendered)
  - /ca/res/topView.php (POST JSON API that populates the list)

No production fixture exists because fetching from Disallowed paths is prohibited.
The parser is a stub returning []. Tests are marked xfail(strict=True) so that
the suite stays green until the robots.txt policy changes or official access is
negotiated.

Real values observed during development recon on 2026-07-02
(mode=1, prd=1 / 1주, val=0 / 전체 — top-30 results):
  Rank 1: sn="2026타경 100495", hit=279
  Rank 2: sn="2024타경 56220",  hit=227
  Rank 3: sn="2025타경 914",    hit=202

See tests/fixtures/dooin/NOTES.md for full details.

To un-defer this task:
  1. Confirm /ca/ or an alternative path is allowed in robots.txt.
  2. Save a real fixture (list.json from /ca/res/topView.php, or list.html
     from a headless render of /ca/caTopView.php).
  3. Implement parse_dooin_list in src/auction_tracker/sources/parse/dooin.py.
  4. Remove the @pytest.mark.xfail decorators below.
"""

from pathlib import Path

import pytest

from auction_tracker.sources.parse.dooin import parse_dooin_list
from auction_tracker.sources.types import SourceName

# Fixture path (does not exist yet — fetching Disallowed by robots.txt)
FIXTURE = Path(__file__).parent.parent / "fixtures" / "dooin" / "list.json"

# Real values from development recon 2026-07-02 (will be used once fixture exists)
EXPECTED_CASE_NO = "2026타경100495"  # sn="2026타경 100495" normalised (space stripped)
EXPECTED_VIEWS = 279


@pytest.mark.xfail(
    strict=True,
    reason=(
        "dooin /ca/ is Disallowed by robots.txt; no fixture saved; "
        "parse_dooin_list is a stub returning []. "
        "See tests/fixtures/dooin/NOTES.md."
    ),
)
def test_parse_dooin_list_extracts_rows():
    rows = parse_dooin_list(FIXTURE.read_text(encoding="utf-8"))
    assert len(rows) >= 1
    by_case = {c: r for c, r in rows}
    assert EXPECTED_CASE_NO in by_case, (
        f"Expected case {EXPECTED_CASE_NO!r} not found in {list(by_case.keys())[:5]}"
    )
    assert by_case[EXPECTED_CASE_NO].source is SourceName.DOOIN
    assert by_case[EXPECTED_CASE_NO].view_count == EXPECTED_VIEWS


@pytest.mark.xfail(
    strict=True,
    reason=(
        "dooin /ca/ is Disallowed by robots.txt; parse_dooin_list is a stub. "
        "See tests/fixtures/dooin/NOTES.md."
    ),
)
def test_parse_dooin_list_returns_thirty_rows():
    """The default API call returns 30 items (TOP30)."""
    rows = parse_dooin_list(FIXTURE.read_text(encoding="utf-8"))
    assert len(rows) == 30


@pytest.mark.xfail(
    strict=True,
    reason=(
        "dooin /ca/ is Disallowed by robots.txt; parse_dooin_list is a stub. "
        "See tests/fixtures/dooin/NOTES.md."
    ),
)
def test_parse_dooin_list_all_sources_are_dooin():
    rows = parse_dooin_list(FIXTURE.read_text(encoding="utf-8"))
    for case_no, result in rows:
        assert result.source is SourceName.DOOIN, f"{case_no} has wrong source"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "dooin /ca/ is Disallowed by robots.txt; parse_dooin_list is a stub. "
        "See tests/fixtures/dooin/NOTES.md."
    ),
)
def test_parse_dooin_list_view_counts_are_ints():
    rows = parse_dooin_list(FIXTURE.read_text(encoding="utf-8"))
    for case_no, result in rows:
        assert isinstance(result.view_count, int), (
            f"{case_no}: expected int view_count, got {type(result.view_count)}"
        )


def test_parse_dooin_list_handles_empty_json():
    """Stub always returns [] — empty input should also return []."""
    assert parse_dooin_list("{}") == []


def test_parse_dooin_list_handles_invalid_input():
    """Stub always returns [] regardless of input."""
    assert parse_dooin_list("not json") == []
