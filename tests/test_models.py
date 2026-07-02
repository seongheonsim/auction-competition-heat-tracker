import datetime as dt

from auction_tracker.models import (
    AuctionResult,
    ComparableCase,
    CompLink,
    DailySnapshot,
    SourceLink,
    WatchlistItem,
)


def test_insert_and_read_watchlist_item(session):
    item = WatchlistItem(
        source_type="court",
        case_no="2024타경12345",
        item_no="1",
        label="○○동 아파트",
    )
    session.add(item)
    session.commit()

    row = session.query(WatchlistItem).one()
    assert row.id is not None
    assert row.active is True
    assert row.added_at is not None


def test_daily_snapshot_stores_raw_json(session):
    item = WatchlistItem(source_type="court", case_no="2024타경1", label="x")
    session.add(item)
    session.commit()
    snap = DailySnapshot(
        watchlist_item_id=item.id,
        source="ggi",
        captured_on=dt.date(2026, 7, 2),
        view_count=123,
        raw={"foo": "bar"},
    )
    session.add(snap)
    session.commit()
    assert session.query(DailySnapshot).one().raw == {"foo": "bar"}


def test_auction_result_and_comparable_and_complink(session):
    comp = ComparableCase(
        source_type="court", case_no="2023타경9", property_type="아파트"
    )
    session.add(comp)
    session.commit()
    result = AuctionResult(
        comparable_case_id=comp.id,
        result_type="매각",
        sale_price=550_000_000,
        sale_ratio=0.91,
        result_date=dt.date(2026, 1, 10),
        source="courtauction",
    )
    session.add(result)
    session.commit()
    assert session.query(AuctionResult).one().sale_price == 550_000_000

    item = WatchlistItem(source_type="court", case_no="2024타경2", label="y")
    session.add(item)
    session.commit()
    link = CompLink(
        comparable_case_id=comp.id,
        watchlist_item_id=item.id,
        match_reason="same type + region",
    )
    session.add(link)
    session.commit()
    assert session.query(CompLink).one().match_reason == "same type + region"


def test_source_link(session):
    item = WatchlistItem(source_type="court", case_no="2024타경3", label="z")
    session.add(item)
    session.commit()
    sl = SourceLink(
        watchlist_item_id=item.id,
        source="ggi",
        external_id_or_url="https://www.ggi.co.kr/...",
        match_status="auto",
    )
    session.add(sl)
    session.commit()
    assert session.query(SourceLink).one().match_status == "auto"
