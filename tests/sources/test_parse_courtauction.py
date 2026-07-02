"""
Tests for parse_courtauction_item.

STATUS: BLOCKED — courtauction.go.kr uses the WebSquare JS framework.
Static HTTP fetching returns the WebSquare shell HTML, not property data.
A parseable fixture cannot be obtained without a headless browser.

All tests are marked xfail until a real fixture (and the expected values
read from it) is available. See tests/fixtures/courtauction/NOTES.md.
"""

import pytest
from pathlib import Path

from auction_tracker.sources.parse.courtauction import parse_courtauction_item
from auction_tracker.sources.types import PropertyFacts, SourceName

FIXTURE = Path(__file__).parent.parent / "fixtures" / "courtauction" / "item.html"


@pytest.mark.xfail(
    reason=(
        "No fixture: courtauction.go.kr requires WebSquare JS runtime "
        "(headless browser) to fetch property data. "
        "See tests/fixtures/courtauction/NOTES.md."
    ),
    strict=True,
)
def test_parse_courtauction_item_extracts_facts():
    """Once a real fixture exists, replace xfail with real expected values from NOTES.md."""
    # These placeholder values MUST be replaced with actual values from NOTES.md
    # once a fixture is obtained.
    EXPECTED_APPRAISAL = None   # <- replace with NOTES.md actual value
    EXPECTED_FAIL_COUNT = None  # <- replace with NOTES.md actual value

    assert FIXTURE.exists(), (
        f"Fixture not found at {FIXTURE}. "
        "Fetch a real courtauction property page via Playwright and save it there."
    )
    facts = parse_courtauction_item(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(facts, PropertyFacts)
    assert facts.source is SourceName.COURTAUCTION
    assert facts.appraisal_price == EXPECTED_APPRAISAL
    assert facts.fail_count == EXPECTED_FAIL_COUNT
