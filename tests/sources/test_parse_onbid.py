"""
Tests for parse_onbid_item.

FIXTURE: tests/fixtures/onbid/item.json
  Fetched: 2026-07-03 from onbid.co.kr via POST inqOrgCltrClg.do (session-cookie only, no login).
  Item: 경상북도 김천시 율곡동 811 103호 근린생활시설
  물건관리번호 (scrnIndctCltrMngNo): 2026-0600-033681
  onbidCltrno: 2027800

EXPECTED values read directly from the saved fixture (item.json):
  cltrApslEvlAvgAmt: 644000000   → appraisal_price
  lowstBidPrc:       381000000   → min_price
  uscbdCnt:          "5"         → fail_count = 5
  pbancPbctCltrStatNm: "입찰진행중" → status
  pbctDdlnDt:        "2026-07-03 16:00" → sale_date = date(2026, 7, 3)

See tests/fixtures/onbid/NOTES.md for full recon details.
"""

from datetime import date
from pathlib import Path

from auction_tracker.sources.parse.onbid import parse_onbid_item
from auction_tracker.sources.types import PropertyFacts, SourceName

FIXTURE = Path(__file__).parent.parent / "fixtures" / "onbid" / "item.json"

# Real values from tests/fixtures/onbid/item.json
EXPECTED_APPRAISAL = 644_000_000    # cltrApslEvlAvgAmt
EXPECTED_MIN_PRICE = 381_000_000    # lowstBidPrc
EXPECTED_FAIL_COUNT = 5             # uscbdCnt (string "5" → int)
EXPECTED_STATUS = "입찰진행중"       # pbancPbctCltrStatNm
EXPECTED_SALE_DATE = date(2026, 7, 3)  # pbctDdlnDt "2026-07-03 16:00"


def test_parse_onbid_item_returns_property_facts():
    facts = parse_onbid_item(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(facts, PropertyFacts)


def test_parse_onbid_item_source_is_onbid():
    facts = parse_onbid_item(FIXTURE.read_text(encoding="utf-8"))
    assert facts.source is SourceName.ONBID


def test_parse_onbid_item_appraisal_price():
    facts = parse_onbid_item(FIXTURE.read_text(encoding="utf-8"))
    assert facts.appraisal_price == EXPECTED_APPRAISAL, (
        f"Expected appraisal_price={EXPECTED_APPRAISAL}, got {facts.appraisal_price}"
    )


def test_parse_onbid_item_min_price():
    facts = parse_onbid_item(FIXTURE.read_text(encoding="utf-8"))
    assert facts.min_price == EXPECTED_MIN_PRICE, (
        f"Expected min_price={EXPECTED_MIN_PRICE}, got {facts.min_price}"
    )


def test_parse_onbid_item_fail_count():
    facts = parse_onbid_item(FIXTURE.read_text(encoding="utf-8"))
    assert facts.fail_count == EXPECTED_FAIL_COUNT, (
        f"Expected fail_count={EXPECTED_FAIL_COUNT}, got {facts.fail_count}"
    )


def test_parse_onbid_item_status():
    facts = parse_onbid_item(FIXTURE.read_text(encoding="utf-8"))
    assert facts.status == EXPECTED_STATUS, (
        f"Expected status={EXPECTED_STATUS!r}, got {facts.status!r}"
    )


def test_parse_onbid_item_sale_date():
    facts = parse_onbid_item(FIXTURE.read_text(encoding="utf-8"))
    assert facts.sale_date == EXPECTED_SALE_DATE, (
        f"Expected sale_date={EXPECTED_SALE_DATE}, got {facts.sale_date}"
    )


def test_parse_onbid_item_result_fields_none_for_active_item():
    """Active 입찰진행중 items have no result data (list API doesn't carry it)."""
    facts = parse_onbid_item(FIXTURE.read_text(encoding="utf-8"))
    assert facts.result_type is None
    assert facts.sale_price is None
    assert facts.result_date is None


def test_parse_onbid_item_raw_preserved():
    """raw dict should contain the original JSON keys."""
    facts = parse_onbid_item(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(facts.raw, dict)
    assert facts.raw.get("onbidCltrno") == "2027800"
    assert facts.raw.get("scrnIndctCltrMngNo") == "2026-0600-033681"


def test_parse_onbid_item_handles_empty_json():
    facts = parse_onbid_item("{}")
    assert isinstance(facts, PropertyFacts)
    assert facts.source is SourceName.ONBID
    assert facts.appraisal_price is None
    assert facts.min_price is None
    assert facts.fail_count is None


def test_parse_onbid_item_handles_invalid_json():
    facts = parse_onbid_item("not json at all")
    assert isinstance(facts, PropertyFacts)
    assert facts.source is SourceName.ONBID
    assert facts.appraisal_price is None


def test_parse_onbid_item_zero_appraisal_is_none():
    """cltrApslEvlAvgAmt=0 (common for some items) should map to None."""
    content = '{"cltrApslEvlAvgAmt": 0, "lowstBidPrc": 100000}'
    facts = parse_onbid_item(content)
    assert facts.appraisal_price is None
    assert facts.min_price == 100_000


def test_parse_onbid_item_zero_min_price_is_none():
    """lowstBidPrc=0 (common for some items) should map to None."""
    content = '{"cltrApslEvlAvgAmt": 500000000, "lowstBidPrc": 0}'
    facts = parse_onbid_item(content)
    assert facts.appraisal_price == 500_000_000
    assert facts.min_price is None
