"""
tankauction.com (탱크옥션) 조회수 파서.

NOTES: The ca/caList.php HTML page is JS-rendered — the list data is NOT present in
the static HTML. Data is served as JSON from the proxied API endpoint:
  GET /api/proxy/api1.php/ca/AuctList.php?pageNo=1&...

This parser accepts the JSON response string returned by that endpoint and extracts
(사건번호, ViewCountResult) tuples.

robots.txt allows /ca/caList.php (the rendered page) but disallows /api (root).
For production use, render caList.php via a headless browser or negotiate official
access. See tests/fixtures/tank/NOTES.md for full recon details.
"""

from __future__ import annotations

import json
from typing import Any

from auction_tracker.sources.types import SourceName, ViewCountResult


def _build_case_no(sn1: int, sn2: int, pn: int) -> str:
    """사건번호 문자열 조립: {sn1}타경{sn2} 또는 {sn1}타경{sn2}({pn})."""
    base = f"{sn1}타경{sn2}"
    return f"{base}({pn})" if pn > 0 else base


def parse_tank_list(json_str: str) -> list[tuple[str, ViewCountResult]]:
    """Parse a tankauction AuctList JSON response string into (사건번호, ViewCountResult).

    Args:
        json_str: JSON string from GET /api/proxy/api1.php/ca/AuctList.php

    Returns:
        List of (case_no, ViewCountResult) tuples; rows missing sn1/sn2 are skipped.
    """
    try:
        payload: dict[str, Any] = json.loads(json_str)
    except json.JSONDecodeError:
        return []

    items = payload.get("items")
    if not isinstance(items, list):
        return []

    results: list[tuple[str, ViewCountResult]] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        sn1 = item.get("sn1")
        sn2 = item.get("sn2")
        if sn1 is None or sn2 is None:
            continue
        try:
            sn1 = int(sn1)
            sn2 = int(sn2)
        except (TypeError, ValueError):
            continue
        if sn1 == 0 and sn2 == 0:
            continue

        pn = int(item.get("pn") or 0)
        case_no = _build_case_no(sn1, sn2, pn)

        hit = item.get("hit")
        view_count = int(hit) if hit is not None else None

        result = ViewCountResult(
            source=SourceName.TANK,
            view_count=view_count,
        )
        results.append((case_no, result))

    return results
