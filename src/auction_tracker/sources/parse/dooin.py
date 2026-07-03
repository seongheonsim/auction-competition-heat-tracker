"""
dooinauction.com (두인경매) 조회수 파서.

DEFERRED — robots.txt Disallows /ca/ in full:

    Disallow: /ca/

Both the view-count ranking page (/ca/caTopView.php) and its JSON data endpoint
(/ca/res/topView.php, POST) are under /ca/ and therefore off-limits for automated
production fetching.

The list page is JS-rendered: <ul id="rsList"> is empty in static HTML and filled
by a jQuery AJAX POST to /ca/res/topView.php returning JSON {"items": [...]}.

Each item would provide:
  - sn   (str)  사건번호, format "YYYY타경 NNNNNN" (space before digits)
  - hit  (int)  조회수 (period view count)

Production use requires either:
  1. A headless browser AND explicit robots.txt permission for /ca/
  2. Official API access negotiated with 두인경매

See tests/fixtures/dooin/NOTES.md for full recon details including real fixture
values observed on 2026-07-02.
"""

from __future__ import annotations

from auction_tracker.sources.types import SourceName, ViewCountResult


def parse_dooin_list(content: str) -> list[tuple[str, ViewCountResult]]:
    """Parse dooin view-count ranking data.

    Currently a stub returning an empty list because the data endpoint
    (POST /ca/res/topView.php) and the ranking page (/ca/caTopView.php)
    are both under Disallow:/ca/ in dooinauction.com/robots.txt.

    Args:
        content: JSON string from POST /ca/res/topView.php (when available).

    Returns:
        Empty list until robots.txt policy permits fetching /ca/ paths.
    """
    # Stub: production fetch path is blocked by robots.txt (Disallow: /ca/)
    return []
