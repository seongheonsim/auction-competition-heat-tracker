import re

_WHITESPACE = re.compile(r"\s+")


def normalize_case_no(raw: str) -> str:
    """사건번호를 표준형으로 정규화한다. 예: '2024 타경 12345' -> '2024타경12345'."""
    if raw is None:
        raise ValueError("case_no is required")
    cleaned = _WHITESPACE.sub("", raw).replace("-", "")
    if not cleaned:
        raise ValueError("case_no is empty after normalization")
    return cleaned
