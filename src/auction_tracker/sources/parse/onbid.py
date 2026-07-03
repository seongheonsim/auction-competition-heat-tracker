"""
onbid.co.kr (한국자산관리공사 온비드) 공매 물건 파서.

Data delivery: XHR/JSON via the list API endpoint (no static HTML).
  POST /op/cltrpbancinf/clbtcltrclg/prptclbtcltrclg/PrptClbtCltrController/inqOrgCltrClg.do
  (also inqCltrClbtRlstClg.do, inqCltrClbtMvastClg.do, inqCltrClbtVhcClg.do for other asset types)

The site homepage JS-redirects to the login page, but a session cookie obtained from
visiting the login page (without actual credentials) is sufficient to call the list AJAX
endpoints. The response Content-Type claims text/html but the body is UTF-8 JSON.

robots.txt: Returns HTTP 404 (no robots.txt file). By RFC 9309 convention, the absence of
robots.txt means all paths are implicitly allowed for crawlers.

See tests/fixtures/onbid/NOTES.md for full recon details (fetch URL, timestamp, raw JSON
values, 물건관리번호 numbering).

물건관리번호 (scrnIndctCltrMngNo) format: YYYY-MMNN-NNNNNN
  e.g. "2026-0600-033681" = year 2026, announcement month/sequence 0600, item 033681

This parser accepts a SINGLE item dict JSON string (one element from cltrInfVOList).
"""

from __future__ import annotations

import json
from typing import Any

from auction_tracker.sources.parse.values import parse_int, parse_kdate
from auction_tracker.sources.types import PropertyFacts, SourceName


def parse_onbid_item(content: str) -> PropertyFacts:
    """Parse a single onbid 공매 물건 JSON dict string into PropertyFacts.

    Args:
        content: JSON string of a single item dict from the onbid list API
                 (one element of ``cltrInfVOList`` in the response from
                 PrptClbtCltrController/inqOrgCltrClg.do or similar endpoints).

    Returns:
        PropertyFacts with populated fields. Returns all-None PropertyFacts
        (source=SourceName.ONBID) on JSON parse error or invalid input.

    Field mapping:
        appraisal_price ← cltrApslEvlAvgAmt (0 treated as None)
        min_price       ← lowstBidPrc (0 treated as None)
        fail_count      ← uscbdCnt (cumulative 유찰 count; "5" → 5)
        status          ← pbancPbctCltrStatNm or pbctCltrStatNm
        sale_date       ← pbctDdlnDt (입찰마감일시, bid deadline date)
        result_type     ← None (not present in list-view items)
        sale_price      ← None (not present in list-view items)
        result_date     ← None (not present in list-view items)
    """
    try:
        item: dict[str, Any] = json.loads(content)
    except (json.JSONDecodeError, TypeError, ValueError):
        return PropertyFacts(source=SourceName.ONBID)

    if not isinstance(item, dict):
        return PropertyFacts(source=SourceName.ONBID)

    # appraisal_price: 평균 감정평가금액 — 0 means "not set", treat as None
    raw_apsl = item.get("cltrApslEvlAvgAmt")
    appraisal_price: int | None = int(raw_apsl) if raw_apsl else None

    # min_price: 최저입찰가 — 0 means "not set", treat as None
    raw_lowst = item.get("lowstBidPrc")
    min_price: int | None = int(raw_lowst) if raw_lowst else None

    # fail_count: uscbdCnt (유찰횟수 누적, stored as string e.g. "5")
    raw_uscbd = item.get("uscbdCnt")
    fail_count: int | None = parse_int(str(raw_uscbd)) if raw_uscbd is not None else None

    # status: 공고물건상태명
    status: str | None = (
        item.get("pbancPbctCltrStatNm") or item.get("pbctCltrStatNm") or None
    )

    # sale_date: 입찰마감일시 (bid deadline) e.g. "2026-07-03 16:00"
    sale_date = parse_kdate(item.get("pbctDdlnDt"))

    # result fields: not available in the list-view API response
    # (completed-item result data lives in a separate bid-result endpoint)
    result_type: str | None = None
    sale_price: int | None = None
    result_date = None

    return PropertyFacts(
        source=SourceName.ONBID,
        appraisal_price=appraisal_price,
        min_price=min_price,
        fail_count=fail_count,
        sale_date=sale_date,
        status=status,
        result_type=result_type,
        sale_price=sale_price,
        result_date=result_date,
        raw=item,
    )
