"""
ggi.co.kr (지지옥션) 조회수 파서.

DEFERRED — robots.txt blocks the entire site for bots:

    User-agent: *
    Disallow: /
    Allow: /main.asp
    Allow: /home.asp

Both the 조회수 TOP50 list page (/search/besttop_list.asp) and its AJAX data
endpoint (/search/besttop_query.asp) are under Disallow:/ and therefore
off-limits for automated production fetching.

Data delivery: The list page is JS-rendered. Data is loaded via jQuery AJAX:

    GET /search/besttop_query.asp

which returns an HTML fragment (not JSON). Each auction card contains:

    <span class="number_letter">3,085</span>   (view count)
    <strong>2023-2003</strong>                 (abbreviated case number YYYY-NNNN)

Case number conversion:
    ggi format  →  standard 사건번호
    2023-2003   →  2023타경2003
    2023-60336[1] → 2023타경60336(1)

Production use requires either:
  1. Explicit robots.txt permission for /search/ paths
  2. Official API/data access negotiated with 지지옥션

See tests/fixtures/ggi/NOTES.md for full recon details including real fixture
values observed on 2026-07-03.
"""

from __future__ import annotations

from auction_tracker.sources.types import SourceName, ViewCountResult


def parse_ggi_list(content: str) -> list[tuple[str, ViewCountResult]]:
    """Parse ggi 조회수 TOP50 HTML fragment.

    Currently a stub returning an empty list because both the list page
    (/search/besttop_list.asp) and the AJAX data endpoint
    (/search/besttop_query.asp) are under Disallow:/ in ggi.co.kr/robots.txt.

    Args:
        content: HTML fragment string from GET /search/besttop_query.asp
                 (when available).

    Returns:
        Empty list until robots.txt policy permits fetching /search/ paths.
    """
    # Stub: production fetch path is blocked by robots.txt (Disallow: /)
    return []
