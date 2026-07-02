from sqlalchemy import select
from sqlalchemy.orm import Session

from auction_tracker.models import WatchlistItem
from auction_tracker.normalize import normalize_case_no


def add_court_item(
    session: Session,
    *,
    case_no: str,
    item_no: str | None,
    label: str,
    region: str | None = None,
    property_type: str | None = None,
) -> WatchlistItem:
    normalized = normalize_case_no(case_no)
    existing = session.scalar(
        select(WatchlistItem).where(
            WatchlistItem.case_no == normalized,
            WatchlistItem.item_no == item_no,
        )
    )
    if existing is not None:
        raise ValueError(f"duplicate court item: {normalized} / {item_no}")
    item = WatchlistItem(
        source_type="court",
        case_no=normalized,
        item_no=item_no,
        label=label,
        region=region,
        property_type=property_type,
    )
    session.add(item)
    session.commit()
    return item


def add_onbid_item(
    session: Session,
    *,
    onbid_no: str,
    label: str,
    region: str | None = None,
    property_type: str | None = None,
) -> WatchlistItem:
    item = WatchlistItem(
        source_type="onbid",
        onbid_no=onbid_no,
        label=label,
        region=region,
        property_type=property_type,
    )
    session.add(item)
    session.commit()
    return item


def list_active(session: Session) -> list[WatchlistItem]:
    return list(
        session.scalars(
            select(WatchlistItem)
            .where(WatchlistItem.active.is_(True))
            .order_by(WatchlistItem.added_at.asc(), WatchlistItem.id.asc())
        )
    )


def get(session: Session, item_id: int) -> WatchlistItem | None:
    return session.get(WatchlistItem, item_id)


def deactivate(session: Session, item_id: int) -> bool:
    item = session.get(WatchlistItem, item_id)
    if item is None:
        return False
    item.active = False
    session.commit()
    return True
