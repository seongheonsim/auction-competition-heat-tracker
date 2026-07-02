from auction_tracker.sources.matching import case_no_matches, pick_matching


def test_case_no_matches_ignoring_format():
    assert case_no_matches("2024타경12345", "2024 타경 12345") is True
    assert case_no_matches("2024타경12345", "2024타경9999") is False


def test_pick_matching_returns_payload():
    cands = [("2024타경1", {"v": 1}), ("2024 타경 2", {"v": 2})]
    assert pick_matching("2024타경2", cands) == {"v": 2}


def test_pick_matching_returns_none_when_absent():
    assert pick_matching("2024타경9", [("2024타경1", 1)]) is None
