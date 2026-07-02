from typing import TypeVar

from auction_tracker.normalize import normalize_case_no

T = TypeVar("T")


def case_no_matches(a: str, b: str) -> bool:
    return normalize_case_no(a) == normalize_case_no(b)


def pick_matching(target_case_no: str, candidates: list[tuple[str, T]]) -> T | None:
    target = normalize_case_no(target_case_no)
    for cand_case_no, payload in candidates:
        try:
            if normalize_case_no(cand_case_no) == target:
                return payload
        except ValueError:
            continue
    return None
