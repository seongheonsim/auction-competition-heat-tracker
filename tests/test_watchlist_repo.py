import pytest

from auction_tracker.repositories import watchlist as repo


def test_add_court_item_normalizes_case_no(session):
    item = repo.add_court_item(
        session, case_no="2024 타경 12345", item_no="1", label="아파트 A"
    )
    assert item.case_no == "2024타경12345"
    assert item.source_type == "court"
    assert item.active is True


def test_add_court_item_rejects_duplicate(session):
    repo.add_court_item(session, case_no="2024타경1", item_no="1", label="A")
    with pytest.raises(ValueError):
        repo.add_court_item(session, case_no="2024 타경 1", item_no="1", label="A dup")


def test_add_onbid_item(session):
    item = repo.add_onbid_item(session, onbid_no="2024-01234-001", label="공매 B")
    assert item.source_type == "onbid"
    assert item.onbid_no == "2024-01234-001"


def test_list_active_excludes_deactivated(session):
    a = repo.add_court_item(session, case_no="2024타경1", item_no="1", label="A")
    b = repo.add_court_item(session, case_no="2024타경2", item_no="1", label="B")
    assert repo.deactivate(session, a.id) is True
    active = repo.list_active(session)
    assert [i.id for i in active] == [b.id]


def test_get_returns_none_for_missing(session):
    assert repo.get(session, 999) is None


def test_deactivate_missing_returns_false(session):
    assert repo.deactivate(session, 999) is False
