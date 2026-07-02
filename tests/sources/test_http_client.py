import httpx
import pytest

from auction_tracker.sources.http_client import DEFAULT_UA, RateLimiter, fetch


def test_rate_limiter_sleeps_when_called_too_soon():
    slept = []
    times = iter([100.0, 100.2, 100.2, 100.2])  # clock() readings
    limiter = RateLimiter(min_interval_s=1.0, sleep=slept.append, clock=lambda: next(times))
    limiter.wait("example.com")   # first call: no sleep, records last=100.0
    limiter.wait("example.com")   # 0.2s elapsed -> must sleep ~0.8s
    assert slept and abs(slept[0] - 0.8) < 1e-6


def test_rate_limiter_independent_per_host():
    times = iter([0.0, 0.0, 5.0, 5.0])
    limiter = RateLimiter(min_interval_s=1.0, sleep=lambda s: (_ for _ in ()).throw(AssertionError("should not sleep")), clock=lambda: next(times))
    limiter.wait("a.com")
    limiter.wait("b.com")  # different host -> no sleep


def test_fetch_returns_text_and_sends_ua():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["ua"] = request.headers.get("user-agent")
        return httpx.Response(200, text="<html>ok</html>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    limiter = RateLimiter(min_interval_s=0.0)
    body = fetch("https://example.com/x", client=client, limiter=limiter, sleep=lambda s: None)
    assert body == "<html>ok</html>"
    assert seen["ua"] == DEFAULT_UA


def test_fetch_retries_then_succeeds():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, text="done")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    limiter = RateLimiter(min_interval_s=0.0)
    body = fetch("https://example.com/y", client=client, limiter=limiter, retries=3, sleep=lambda s: None)
    assert body == "done"
    assert calls["n"] == 3


def test_fetch_raises_after_exhausting_retries():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    limiter = RateLimiter(min_interval_s=0.0)
    with pytest.raises(httpx.HTTPStatusError):
        fetch("https://example.com/z", client=client, limiter=limiter, retries=2, sleep=lambda s: None)
