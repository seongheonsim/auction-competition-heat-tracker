from typing import Optional, Protocol, runtime_checkable

from auction_tracker.sources.types import PropertyFacts, SourceName, ViewCountResult


@runtime_checkable
class FactsAdapter(Protocol):
    source: SourceName

    def fetch_facts(
        self,
        *,
        case_no: Optional[str] = None,
        item_no: Optional[str] = None,
        onbid_no: Optional[str] = None,
    ) -> Optional[PropertyFacts]: ...


@runtime_checkable
class ViewCountAdapter(Protocol):
    source: SourceName

    def fetch_view_count(
        self,
        *,
        case_no: str,
        item_no: Optional[str] = None,
    ) -> Optional[ViewCountResult]: ...
