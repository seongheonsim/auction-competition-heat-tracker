from typing import Callable, Optional

import httpx

from auction_tracker.sources.matching import pick_matching
from auction_tracker.sources.parse.tank import parse_tank_list
from auction_tracker.sources.types import SourceError, SourceName, ViewCountResult


class TankAdapter:
    source = SourceName.TANK

    def __init__(self, fetcher: Callable[[str], str]) -> None:
        self._fetcher = fetcher

    def fetch_view_count(
        self, *, case_no: str, item_no: Optional[str] = None
    ) -> Optional[ViewCountResult]:
        try:
            content = self._fetcher(case_no)
        except httpx.HTTPError as exc:
            raise SourceError(self.source, f"fetch failed: {exc}") from exc
        rows = parse_tank_list(content)
        return pick_matching(case_no, rows)
