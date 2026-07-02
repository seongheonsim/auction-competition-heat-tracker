import datetime as dt
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> dt.datetime:
    return dt.datetime.now(tz=dt.timezone.utc)


class Base(DeclarativeBase):
    pass


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_type: Mapped[str] = mapped_column(String(16))  # court | onbid
    case_no: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    item_no: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    onbid_no: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    label: Mapped[str] = mapped_column(String(200))
    region: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    property_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    added_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class SourceLink(Base):
    __tablename__ = "source_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    watchlist_item_id: Mapped[int] = mapped_column(ForeignKey("watchlist_items.id"))
    source: Mapped[str] = mapped_column(String(16))  # ggi | tank | dooin
    external_id_or_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    match_status: Mapped[str] = mapped_column(String(16), default="unmatched")


class DailySnapshot(Base):
    __tablename__ = "daily_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    watchlist_item_id: Mapped[int] = mapped_column(ForeignKey("watchlist_items.id"))
    source: Mapped[str] = mapped_column(String(16))
    captured_on: Mapped[dt.date] = mapped_column(Date)
    view_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    appraisal_price: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    min_price: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    fail_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sale_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    raw: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)


class ComparableCase(Base):
    __tablename__ = "comparable_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_type: Mapped[str] = mapped_column(String(16))
    case_no: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    onbid_no: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    property_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    appraisal_price: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    fail_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class AuctionResult(Base):
    __tablename__ = "auction_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    watchlist_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("watchlist_items.id"), nullable=True
    )
    comparable_case_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("comparable_cases.id"), nullable=True
    )
    result_type: Mapped[str] = mapped_column(String(24))  # 매각 | 유찰 | 취하 | 변경 | 재매각
    sale_price: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    sale_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    result_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    source: Mapped[str] = mapped_column(String(16))
    raw: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)


class CompLink(Base):
    __tablename__ = "comp_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comparable_case_id: Mapped[int] = mapped_column(ForeignKey("comparable_cases.id"))
    watchlist_item_id: Mapped[int] = mapped_column(ForeignKey("watchlist_items.id"))
    match_reason: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
