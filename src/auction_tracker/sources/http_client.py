import time
from typing import Callable

import httpx

DEFAULT_UA = "Mozilla/5.0 (compatible; auction-tracker/0.1; personal-use)"


class RateLimiter:
    def __init__(
        self,
        min_interval_s: float,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.min_interval_s = min_interval_s
        self._sleep = sleep
        self._clock = clock
        self._last: dict[str, float] = {}

    def wait(self, host: str) -> None:
        last = self._last.get(host)
        if last is not None:
            elapsed = self._clock() - last
            remaining = self.min_interval_s - elapsed
            if remaining > 0:
                self._sleep(remaining)
        self._last[host] = self._clock()


def fetch(
    url: str,
    *,
    client: httpx.Client,
    limiter: RateLimiter,
    retries: int = 3,
    backoff_base: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    host = httpx.URL(url).host
    last_exc: Exception | None = None
    for attempt in range(retries):
        limiter.wait(host)
        try:
            resp = client.get(url, headers={"User-Agent": DEFAULT_UA}, timeout=20.0)
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPError as exc:
            last_exc = exc
            if attempt == retries - 1:
                raise
            sleep(backoff_base * (2 ** attempt))
    raise last_exc  # unreachable, for type-checkers
