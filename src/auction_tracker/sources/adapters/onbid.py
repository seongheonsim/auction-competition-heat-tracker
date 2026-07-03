from typing import Callable, Optional

import httpx

from auction_tracker.sources.parse.onbid import parse_onbid_item
from auction_tracker.sources.types import PropertyFacts, SourceError, SourceName


class OnbidAdapter:
    source = SourceName.ONBID

    def __init__(self, fetcher: Callable[[str], str]) -> None:
        self._fetcher = fetcher

    def fetch_facts(
        self,
        *,
        case_no: Optional[str] = None,
        item_no: Optional[str] = None,
        onbid_no: Optional[str] = None,
    ) -> Optional[PropertyFacts]:
        if not onbid_no:
            return None
        try:
            content = self._fetcher(onbid_no)
        except httpx.HTTPError as exc:
            raise SourceError(self.source, f"fetch failed: {exc}") from exc
        return parse_onbid_item(content)
