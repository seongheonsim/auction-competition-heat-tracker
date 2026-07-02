import pytest

from auction_tracker.normalize import normalize_case_no


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2024타경12345", "2024타경12345"),
        ("2024 타경 12345", "2024타경12345"),
        (" 2024타경-12345 ", "2024타경12345"),
        ("2024\t타경\n12345", "2024타경12345"),
    ],
)
def test_normalize_case_no(raw, expected):
    assert normalize_case_no(raw) == expected


def test_normalize_case_no_rejects_empty():
    with pytest.raises(ValueError):
        normalize_case_no("   ")
