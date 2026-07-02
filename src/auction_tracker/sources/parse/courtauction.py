"""
courtauction.go.kr item parser.

STATUS: BLOCKED — courtauction.go.kr uses the WebSquare JS framework and does
not serve static HTML for property detail pages. All data endpoints require a
live WebSquare runtime session (headless browser or session token reverse-engineering).
See tests/fixtures/courtauction/NOTES.md for full recon findings and alternative
approaches.

This module is a placeholder. It will be implemented once a fixture can be
obtained via Playwright or an official open-data API.
"""

from auction_tracker.sources.types import PropertyFacts, SourceName


def parse_courtauction_item(html: str) -> PropertyFacts:
    """Parse a courtauction.go.kr property detail page into PropertyFacts.

    NOTE: Not yet implemented — see module docstring and NOTES.md.
    Returns a PropertyFacts with all fields None until a parseable fixture
    is available.
    """
    return PropertyFacts(source=SourceName.COURTAUCTION)
