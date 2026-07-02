from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Optional


class SourceName(str, Enum):
    COURTAUCTION = "courtauction"
    ONBID = "onbid"
    GGI = "ggi"
    TANK = "tank"
    DOOIN = "dooin"


@dataclass
class PropertyFacts:
    source: SourceName
    appraisal_price: Optional[int] = None
    min_price: Optional[int] = None
    fail_count: Optional[int] = None
    sale_date: Optional[date] = None
    status: Optional[str] = None
    result_type: Optional[str] = None
    sale_price: Optional[int] = None
    result_date: Optional[date] = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ViewCountResult:
    source: SourceName
    view_count: Optional[int] = None
    sale_ratio: Optional[float] = None
    raw: dict[str, Any] = field(default_factory=dict)


class SourceError(Exception):
    def __init__(self, source: SourceName, message: str) -> None:
        super().__init__(f"[{source.value}] {message}")
        self.source = source
        self.message = message
