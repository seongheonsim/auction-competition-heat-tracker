import re
from datetime import date

_DIGITS = re.compile(r"\d+")


def parse_money(s: str | None) -> int | None:
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", s)
    return int(digits) if digits else None


def parse_int(s: str | None) -> int | None:
    if not s:
        return None
    m = _DIGITS.search(s.replace(",", ""))
    return int(m.group()) if m else None


def parse_kdate(s: str | None) -> date | None:
    if not s:
        return None
    m = re.search(r"(\d{4})[.\-](\d{1,2})[.\-](\d{1,2})", s)
    if not m:
        return None
    y, mo, d = (int(x) for x in m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None
