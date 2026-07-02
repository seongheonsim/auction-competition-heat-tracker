# Plan 2a — 어댑터 프레임워크 & 파서 & 매칭 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 5개 경매정보 소스(courtauction·onbid·ggi·tank·dooin)에서 "물건 식별자 → 표준화된 데이터(기본정보/조회수/매각결과)"를 반환하는 어댑터 계층을 만든다. 파싱은 네트워크와 분리해 저장된 HTML 픽스처로 오프라인 검증한다.

**Architecture:** `sources` 패키지에 (1) 표준 결과 타입, (2) 요청제한·재시도 HTTP 클라이언트, (3) 어댑터 프로토콜, (4) 사이트별 **순수 파싱 함수**(HTML 문자열→데이터, 픽스처로 TDD), (5) 파싱+페치를 묶는 어댑터, (6) 사건번호 기반 매칭을 둔다. 파싱 함수는 네트워크를 타지 않으므로 저장된 HTML 픽스처만으로 단위테스트한다. 실제 셀렉터는 각 파서 태스크의 recon 단계에서 확보한 픽스처를 기준으로 작성한다.

**Tech Stack:** Python 3.12 · uv · httpx(HTTP) · beautifulsoup4 + lxml(HTML 파싱) · pytest. (Plan 1의 config/db/models/normalize/repositories 위에 얹는다.)

## Global Constraints

- Python 3.12 · 패키지 관리 uv (`uv add`, `uv run pytest`) · src-layout `src/auction_tracker/` · 테스트 `tests/`.
- Conventional Commits · 타임스탬프는 timezone-aware UTC.
- **파싱과 네트워크 분리**: 순수 파싱 함수는 `str`(HTML) → dataclass만 다루고 절대 네트워크를 타지 않는다. 파싱 단위테스트는 실사이트 호출 없이 `tests/fixtures/<source>/*.html`로만 돈다.
- **유료 사이트 저부하 원칙**: 어댑터 페치는 요청 간 최소 간격(host별)·표준 User-Agent·지수 백오프 재시도를 거친다. recon(라이브 페치)은 사이트당 최소 횟수만.
- **책임 스크래핑**: 각 파서 태스크의 recon 단계에서 해당 사이트 `robots.txt`를 확인하고, 확인 결과를 fixture 옆 `NOTES.md`에 남긴다.
- 표준 타입·시그니처는 이 플랜에서 확정하며, Plan 2b(크롤러)·2c(집계)가 이를 그대로 소비한다.

---

## 실행 노트 (2026-07-02, recon 결과 반영)

- **courtauction.go.kr = WebSquare(JS 프레임워크)** — 정적 GET/POST로 물건 데이터 취득 불가. Task 5 PART B는 stub + `@pytest.mark.xfail(strict=True)` + `tests/fixtures/courtauction/NOTES.md`(대안 기록)로 두고, **헤드리스 브라우저(Playwright) 기반 별도 플랜으로 연기**한다.
- 사용자 결정: **정적 사이트 먼저, JS는 나중.** 홈페이지 프로브상 tank·dooin은 서버렌더링(정적 유망), ggi·onbid은 응답이 작아 JS/리다이렉트 의심.
- **파서 태스크 실행 순서 조정:** Task 8(tank) → Task 9(dooin) → Task 7(ggi) → Task 6(onbid). 각 recon에서 로그인 없이 조회수(또는 facts)가 정적 HTML로 보이면 구현, JS라 불가하면 courtauction과 동일하게 stub+xfail+NOTES로 연기한다.
- **Task 10(어댑터)** 는 실제로 파서가 구현된 소스에 대해서만 어댑터를 완성하고, 연기된 소스는 어댑터도 함께 연기한다.

---

## File Structure

- `src/auction_tracker/sources/__init__.py` — 패키지 마커
- `src/auction_tracker/sources/types.py` — `SourceName`(enum), `PropertyFacts`, `ViewCountResult`, `SourceError`
- `src/auction_tracker/sources/http_client.py` — `RateLimiter`, `fetch()`
- `src/auction_tracker/sources/base.py` — `FactsAdapter`/`ViewCountAdapter` 프로토콜
- `src/auction_tracker/sources/matching.py` — 사건번호 매칭 헬퍼
- `src/auction_tracker/sources/parse/__init__.py`
- `src/auction_tracker/sources/parse/courtauction.py` · `onbid.py` · `ggi.py` · `tank.py` · `dooin.py` — 순수 파싱 함수
- `src/auction_tracker/sources/adapters/__init__.py`
- `src/auction_tracker/sources/adapters/courtauction.py` · `onbid.py` · `ggi.py` · `tank.py` · `dooin.py` — 페치+파싱 어댑터
- `tests/fixtures/<source>/*.html` — recon으로 저장한 실제 페이지 샘플 + `NOTES.md`
- `tests/sources/test_*.py` — 파싱·클라이언트·매칭 테스트

---

### Task 1: 표준 결과 타입

**Files:**
- Create: `src/auction_tracker/sources/__init__.py` (빈 파일), `src/auction_tracker/sources/types.py`
- Test: `tests/sources/__init__.py` (빈 파일), `tests/sources/test_types.py`

**Interfaces:**
- Consumes: (없음)
- Produces:
  - `SourceName(str, Enum)`: `COURTAUCTION="courtauction"`, `ONBID="onbid"`, `GGI="ggi"`, `TANK="tank"`, `DOOIN="dooin"`.
  - `PropertyFacts` dataclass: `source: SourceName`, `appraisal_price: int|None`, `min_price: int|None`, `fail_count: int|None`, `sale_date: date|None`, `status: str|None`, `result_type: str|None`, `sale_price: int|None`, `result_date: date|None`, `raw: dict`.
  - `ViewCountResult` dataclass: `source: SourceName`, `view_count: int|None`, `sale_ratio: float|None`, `raw: dict`.
  - `SourceError(Exception)`: 속성 `source: SourceName`, `message: str`.

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/sources/test_types.py`
```python
import datetime as dt

from auction_tracker.sources.types import (
    PropertyFacts,
    SourceError,
    SourceName,
    ViewCountResult,
)


def test_source_name_values():
    assert SourceName.GGI.value == "ggi"
    assert SourceName("courtauction") is SourceName.COURTAUCTION


def test_property_facts_defaults():
    f = PropertyFacts(source=SourceName.COURTAUCTION)
    assert f.appraisal_price is None
    assert f.raw == {}
    f2 = PropertyFacts(source=SourceName.COURTAUCTION, sale_price=100, result_type="매각")
    assert f2.sale_price == 100 and f2.result_type == "매각"


def test_view_count_result_defaults():
    v = ViewCountResult(source=SourceName.GGI, view_count=42)
    assert v.view_count == 42
    assert v.sale_ratio is None
    assert v.raw == {}


def test_source_error_carries_source():
    err = SourceError(SourceName.TANK, "parse failed")
    assert err.source is SourceName.TANK
    assert "tank" in str(err)
    assert err.message == "parse failed"
```

- [ ] **Step 2: 실패 확인** — Run: `uv run pytest tests/sources/test_types.py -v` → FAIL (ModuleNotFoundError).

- [ ] **Step 3: 구현** — `tests/sources/__init__.py`는 빈 파일. `src/auction_tracker/sources/__init__.py`도 빈 파일. `src/auction_tracker/sources/types.py`:
```python
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
```

- [ ] **Step 4: 통과 확인** — Run: `uv run pytest tests/sources/test_types.py -v` → PASS (4 passed).

- [ ] **Step 5: 커밋**
```bash
git add src/auction_tracker/sources/__init__.py src/auction_tracker/sources/types.py tests/sources/__init__.py tests/sources/test_types.py
git commit -m "feat: add standardized source result types"
```

---

### Task 2: 요청제한·재시도 HTTP 클라이언트

**Files:**
- Create: `src/auction_tracker/sources/http_client.py`
- Test: `tests/sources/test_http_client.py`
- Modify: `pyproject.toml` (httpx 의존성 추가)

**Interfaces:**
- Consumes: (없음)
- Produces:
  - `DEFAULT_UA: str`
  - `RateLimiter(min_interval_s: float, sleep=time.sleep, clock=time.monotonic)` — 메서드 `wait(host: str) -> None`: 같은 host에 대해 직전 호출로부터 `min_interval_s`가 안 지났으면 남은 시간만큼 `sleep`.
  - `fetch(url: str, *, client: httpx.Client, limiter: RateLimiter, retries: int = 3, backoff_base: float = 1.0, sleep=time.sleep) -> str` — host별 rate limit 적용 후 GET, `raise_for_status()`, 실패 시 지수 백오프 재시도, 마지막 시도 실패면 예외 전파. 성공 시 `resp.text` 반환.

- [ ] **Step 1: httpx 추가** — Run: `uv add httpx`

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/sources/test_http_client.py`
```python
import httpx
import pytest

from auction_tracker.sources.http_client import DEFAULT_UA, RateLimiter, fetch


def test_rate_limiter_sleeps_when_called_too_soon():
    slept = []
    times = iter([100.0, 100.0, 100.2, 100.2])  # clock() readings
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
```

- [ ] **Step 3: 실패 확인** — Run: `uv run pytest tests/sources/test_http_client.py -v` → FAIL (ModuleNotFoundError).

- [ ] **Step 4: 구현** — `src/auction_tracker/sources/http_client.py`
```python
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
```

- [ ] **Step 5: 통과 확인** — Run: `uv run pytest tests/sources/test_http_client.py -v` → PASS (5 passed).

- [ ] **Step 6: 커밋**
```bash
git add pyproject.toml uv.lock src/auction_tracker/sources/http_client.py tests/sources/test_http_client.py
git commit -m "feat: add rate-limited retrying http client"
```

---

### Task 3: 어댑터 프로토콜

**Files:**
- Create: `src/auction_tracker/sources/base.py`
- Test: `tests/sources/test_base.py`

**Interfaces:**
- Consumes: `sources.types` (`PropertyFacts`, `ViewCountResult`)
- Produces (typing.Protocol, 런타임 검사용 `@runtime_checkable`):
  - `FactsAdapter`: 속성 `source: SourceName`; 메서드 `fetch_facts(self, *, case_no: str | None, item_no: str | None, onbid_no: str | None) -> PropertyFacts | None`.
  - `ViewCountAdapter`: 속성 `source: SourceName`; 메서드 `fetch_view_count(self, *, case_no: str, item_no: str | None) -> ViewCountResult | None`.

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/sources/test_base.py`
```python
from auction_tracker.sources.base import FactsAdapter, ViewCountAdapter
from auction_tracker.sources.types import PropertyFacts, SourceName, ViewCountResult


class _FakeFacts:
    source = SourceName.COURTAUCTION

    def fetch_facts(self, *, case_no=None, item_no=None, onbid_no=None):
        return PropertyFacts(source=self.source, appraisal_price=1)


class _FakeViews:
    source = SourceName.GGI

    def fetch_view_count(self, *, case_no, item_no=None):
        return ViewCountResult(source=self.source, view_count=7)


def test_facts_adapter_runtime_checkable():
    assert isinstance(_FakeFacts(), FactsAdapter)
    assert not isinstance(_FakeViews(), FactsAdapter)


def test_view_count_adapter_runtime_checkable():
    assert isinstance(_FakeViews(), ViewCountAdapter)
    assert not isinstance(_FakeFacts(), ViewCountAdapter)
```

- [ ] **Step 2: 실패 확인** — Run: `uv run pytest tests/sources/test_base.py -v` → FAIL (ModuleNotFoundError).

- [ ] **Step 3: 구현** — `src/auction_tracker/sources/base.py`
```python
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
```

- [ ] **Step 4: 통과 확인** — Run: `uv run pytest tests/sources/test_base.py -v` → PASS (2 passed).

- [ ] **Step 5: 커밋**
```bash
git add src/auction_tracker/sources/base.py tests/sources/test_base.py
git commit -m "feat: add source adapter protocols"
```

---

### Task 4: 사건번호 매칭 헬퍼

**Files:**
- Create: `src/auction_tracker/sources/matching.py`
- Test: `tests/sources/test_matching.py`

**Interfaces:**
- Consumes: `auction_tracker.normalize.normalize_case_no`
- Produces:
  - `case_no_matches(a: str, b: str) -> bool` — 정규화 후 동등 비교.
  - `pick_matching(target_case_no: str, candidates: list[tuple[str, T]]) -> T | None` — `(candidate_case_no, payload)` 리스트에서 target과 매칭되는 첫 payload 반환, 없으면 None.

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/sources/test_matching.py`
```python
from auction_tracker.sources.matching import case_no_matches, pick_matching


def test_case_no_matches_ignoring_format():
    assert case_no_matches("2024타경12345", "2024 타경 12345") is True
    assert case_no_matches("2024타경12345", "2024타경9999") is False


def test_pick_matching_returns_payload():
    cands = [("2024타경1", {"v": 1}), ("2024 타경 2", {"v": 2})]
    assert pick_matching("2024타경2", cands) == {"v": 2}


def test_pick_matching_returns_none_when_absent():
    assert pick_matching("2024타경9", [("2024타경1", 1)]) is None
```

- [ ] **Step 2: 실패 확인** — Run: `uv run pytest tests/sources/test_matching.py -v` → FAIL (ModuleNotFoundError).

- [ ] **Step 3: 구현** — `src/auction_tracker/sources/matching.py`
```python
from typing import TypeVar

from auction_tracker.normalize import normalize_case_no

T = TypeVar("T")


def case_no_matches(a: str, b: str) -> bool:
    return normalize_case_no(a) == normalize_case_no(b)


def pick_matching(target_case_no: str, candidates: list[tuple[str, T]]) -> T | None:
    target = normalize_case_no(target_case_no)
    for cand_case_no, payload in candidates:
        try:
            if normalize_case_no(cand_case_no) == target:
                return payload
        except ValueError:
            continue
    return None
```

- [ ] **Step 4: 통과 확인** — Run: `uv run pytest tests/sources/test_matching.py -v` → PASS (3 passed).

- [ ] **Step 5: 커밋**
```bash
git add src/auction_tracker/sources/matching.py tests/sources/test_matching.py
git commit -m "feat: add case-number matching helpers"
```

---

## 파서 태스크 공통 절차 (Task 5~9)

각 파서 태스크는 **동일한 4단계 패턴**을 따른다. 사이트별로 실제 HTML을 모르므로, recon으로 픽스처를 확보한 뒤 그 픽스처의 **실제 값**을 기준으로 테스트를 작성한다.

1. **recon(라이브 1회 페치)**: 해당 사이트에서 대상 페이지 1개를 실제로 가져와 `tests/fixtures/<source>/<name>.html`로 저장한다. `bs4`로 파싱 가능한 HTML인지 확인한다. 같은 폴더 `NOTES.md`에 기록: 페치한 URL, 페치 시각, `robots.txt` 확인 결과(허용/주의사항), 그리고 **육안으로 읽은 실제 값**(예: 감정가 552,000,000 / 조회수 1,234 / 사건번호 2024타경12345). 이 값들이 테스트의 기대값이 된다.
   - recon 페치에는 Task 2의 `fetch()`(rate limit·UA 포함)를 쓰거나, 동등하게 `httpx.get`에 `DEFAULT_UA`를 붙여 1회만 호출한다. 유료 사이트는 **로그인 없이 목록/요약 페이지**만 대상으로 한다(스펙 원칙).
2. **파싱 함수 테스트 작성**: 저장한 픽스처를 읽어 파싱 함수에 넣고, NOTES.md에 적은 실제 값과 일치하는지 assert. 네트워크 호출 없음.
3. **파싱 함수 구현**: bs4/lxml 셀렉터로 필요한 필드를 추출. 값 파싱은 아래 헬퍼로 통일한다(Task 5에서 함께 만든다):
   - 금액 문자열 → int: 쉼표·"원"·공백 제거 후 int. (예: `"552,000,000원"` → `552000000`)
   - 정수 문자열 → int: 숫자 외 문자 제거.
   - 날짜 문자열 → date: `YYYY.MM.DD` / `YYYY-MM-DD` 모두 허용.
4. **어댑터 구현**: 페치 URL 구성 + `fetch()` 호출 + 파싱 함수 연결 + 예외를 `SourceError`로 변환. 어댑터 테스트는 `fetch`를 주입 가능한 형태로 두고 저장된 픽스처 문자열을 반환하는 fake fetch로 검증(네트워크 없음).

**주의(정직성):** 실제 셀렉터 코드는 recon 픽스처 없이는 정확히 알 수 없다. 따라서 아래 각 파서 태스크는 **함수 시그니처·반환 타입·테스트 골격·추출 대상 필드**를 확정해 두고, 셀렉터 구현부만 recon 픽스처를 보고 채운다. 반환 타입은 Task 1의 `PropertyFacts`/`ViewCountResult`로 고정이다.

---

### Task 5: 파싱 값 헬퍼 + courtauction 파서

**Files:**
- Create: `src/auction_tracker/sources/parse/__init__.py`(빈 파일), `src/auction_tracker/sources/parse/values.py`, `src/auction_tracker/sources/parse/courtauction.py`
- Create(recon): `tests/fixtures/courtauction/item.html`, `tests/fixtures/courtauction/NOTES.md`
- Test: `tests/sources/test_parse_values.py`, `tests/sources/test_parse_courtauction.py`
- Modify: `pyproject.toml` (beautifulsoup4, lxml 추가)

**Interfaces:**
- Consumes: `sources.types.PropertyFacts`, `SourceName`
- Produces:
  - `parse/values.py`: `parse_money(s: str) -> int | None`, `parse_int(s: str) -> int | None`, `parse_kdate(s: str) -> date | None`. 빈/파싱불가 입력은 `None`.
  - `parse/courtauction.py`: `parse_courtauction_item(html: str) -> PropertyFacts`. 추출: appraisal_price, min_price, fail_count, sale_date, status, (개찰 후) result_type/sale_price/result_date. 원문 일부를 `raw`에 보관.

- [ ] **Step 1: 의존성 추가** — Run: `uv add beautifulsoup4 lxml`

- [ ] **Step 2: 값 헬퍼 테스트 작성** — `tests/sources/test_parse_values.py`
```python
import datetime as dt

from auction_tracker.sources.parse.values import parse_int, parse_kdate, parse_money


def test_parse_money():
    assert parse_money("552,000,000원") == 552000000
    assert parse_money(" 1,234 ") == 1234
    assert parse_money("") is None
    assert parse_money("-") is None


def test_parse_int():
    assert parse_int("유찰 2회") == 2
    assert parse_int("1,234") == 1234
    assert parse_int("없음") is None


def test_parse_kdate():
    assert parse_kdate("2026.07.02") == dt.date(2026, 7, 2)
    assert parse_kdate("2026-07-02") == dt.date(2026, 7, 2)
    assert parse_kdate("미정") is None
```

- [ ] **Step 3: 값 헬퍼 실패 확인 후 구현** — Run: `uv run pytest tests/sources/test_parse_values.py -v` → FAIL. 그다음 `src/auction_tracker/sources/parse/__init__.py`(빈 파일)과 `src/auction_tracker/sources/parse/values.py`:
```python
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
```
Run: `uv run pytest tests/sources/test_parse_values.py -v` → PASS (3 passed).

- [ ] **Step 4: recon — courtauction 픽스처 확보**
  - 대법원 경매정보(courtauction.go.kr)에서 진행 중이거나 종료된 물건 상세 페이지 1개의 HTML을 가져와 `tests/fixtures/courtauction/item.html`로 저장한다. (Task 2 `fetch()` 또는 `httpx.get(url, headers={"User-Agent": DEFAULT_UA})` 1회.)
  - `robots.txt` 확인 후 `tests/fixtures/courtauction/NOTES.md`에 URL·시각·robots 결과·육안 실제 값(감정가/최저가/유찰횟수/매각기일/상태, 종료물건이면 매각결과·매각가)을 적는다.
  - 만약 courtauction이 JS 렌더링/세션 없이는 상세를 안 주면, 접근 가능한 목록/요약 페이지로 범위를 좁히고 그 사실을 NOTES.md에 남긴다(무엇을 추출 가능한지 재조정).

- [ ] **Step 5: courtauction 파싱 테스트 작성** — `tests/sources/test_parse_courtauction.py` (NOTES.md의 실제 값으로 `EXPECTED_*`를 채운다)
```python
from pathlib import Path

from auction_tracker.sources.parse.courtauction import parse_courtauction_item
from auction_tracker.sources.types import PropertyFacts, SourceName

FIXTURE = Path(__file__).parent.parent / "fixtures" / "courtauction" / "item.html"

# recon(NOTES.md)에서 확인한 실제 값으로 교체:
EXPECTED_APPRAISAL = 552000000  # <- NOTES.md 실제 값
EXPECTED_FAIL_COUNT = 1         # <- NOTES.md 실제 값


def test_parse_courtauction_item_extracts_facts():
    facts = parse_courtauction_item(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(facts, PropertyFacts)
    assert facts.source is SourceName.COURTAUCTION
    assert facts.appraisal_price == EXPECTED_APPRAISAL
    assert facts.fail_count == EXPECTED_FAIL_COUNT
    # min_price/sale_date 등 NOTES.md에서 확인 가능한 필드에 대한 assert를 추가한다.
```

- [ ] **Step 6: courtauction 파서 구현** — `src/auction_tracker/sources/parse/courtauction.py`. bs4로 픽스처의 실제 구조에 맞춰 셀렉터 작성, `parse_money`/`parse_int`/`parse_kdate` 사용, `PropertyFacts(source=SourceName.COURTAUCTION, ...)` 반환. 파싱 실패 필드는 None으로 두되, 핵심 표(감정가 등)를 아예 못 찾으면 `SourceError`를 던지지 말고 값이 None인 PropertyFacts를 반환한다(어댑터 계층에서 unmatched 판단). Run: `uv run pytest tests/sources/test_parse_courtauction.py -v` → PASS.

- [ ] **Step 7: 커밋**
```bash
git add pyproject.toml uv.lock src/auction_tracker/sources/parse/ tests/fixtures/courtauction/ tests/sources/test_parse_values.py tests/sources/test_parse_courtauction.py
git commit -m "feat: add parse value helpers and courtauction item parser"
```

---

### Task 6: onbid 파서

**Files:**
- Create: `src/auction_tracker/sources/parse/onbid.py`, `tests/fixtures/onbid/item.html`, `tests/fixtures/onbid/NOTES.md`
- Test: `tests/sources/test_parse_onbid.py`

**Interfaces:**
- Consumes: `sources.types.PropertyFacts`, `SourceName`, `parse.values`
- Produces: `parse_onbid_item(html: str) -> PropertyFacts` (source=`ONBID`). 추출: appraisal_price, min_price, fail_count(있으면), sale_date, status, (종료 시) result_type/sale_price/result_date.

절차는 위 "파서 태스크 공통 절차"를 따른다.

- [ ] **Step 1: recon** — onbid.co.kr 공매 물건 상세/요약 페이지 1개 HTML을 `tests/fixtures/onbid/item.html`로 저장, `NOTES.md`에 URL·시각·robots·실제 값 기록. 공매 번호 체계(물건관리번호)도 기록한다.

- [ ] **Step 2: 파싱 테스트 작성** — `tests/sources/test_parse_onbid.py`
```python
from pathlib import Path

from auction_tracker.sources.parse.onbid import parse_onbid_item
from auction_tracker.sources.types import PropertyFacts, SourceName

FIXTURE = Path(__file__).parent.parent / "fixtures" / "onbid" / "item.html"

EXPECTED_APPRAISAL = 0  # <- NOTES.md 실제 값으로 교체


def test_parse_onbid_item_extracts_facts():
    facts = parse_onbid_item(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(facts, PropertyFacts)
    assert facts.source is SourceName.ONBID
    assert facts.appraisal_price == EXPECTED_APPRAISAL
    # NOTES.md에서 확인 가능한 다른 필드 assert 추가
```

- [ ] **Step 3: 실패 확인 후 구현** — `parse_onbid_item` 구현(bs4 + values 헬퍼). Run: `uv run pytest tests/sources/test_parse_onbid.py -v` → PASS.

- [ ] **Step 4: 커밋**
```bash
git add src/auction_tracker/sources/parse/onbid.py tests/fixtures/onbid/ tests/sources/test_parse_onbid.py
git commit -m "feat: add onbid item parser"
```

---

### Task 7: ggi(지지옥션) 조회수 파서

**Files:**
- Create: `src/auction_tracker/sources/parse/ggi.py`, `tests/fixtures/ggi/list.html`, `tests/fixtures/ggi/NOTES.md`
- Test: `tests/sources/test_parse_ggi.py`

**Interfaces:**
- Consumes: `sources.types.ViewCountResult`, `SourceName`, `parse.values`
- Produces: `parse_ggi_list(html: str) -> list[tuple[str, ViewCountResult]]` — 목록 페이지에서 `(사건번호, ViewCountResult(view_count=..., sale_ratio=완료건이면))` 튜플 리스트. 매칭(Task 4 `pick_matching`)에 그대로 넘길 형태.

절차는 "파서 태스크 공통 절차"를 따른다(유료 사이트: **로그인 없이 보이는 목록** 페이지만).

- [ ] **Step 1: recon** — ggi.co.kr 목록 페이지(로그인 없이 조회수가 보이는 화면) 1개 HTML을 `tests/fixtures/ggi/list.html`로 저장. NOTES.md에 URL·시각·robots·행 몇 개의 실제 (사건번호, 조회수) 값 기록. 조회수가 로그인 없이 안 보이면 그 사실을 NOTES.md에 남기고, 보이는 대체 지표(있으면)를 기록한다.

- [ ] **Step 2: 파싱 테스트 작성** — `tests/sources/test_parse_ggi.py`
```python
from pathlib import Path

from auction_tracker.sources.parse.ggi import parse_ggi_list
from auction_tracker.sources.types import SourceName

FIXTURE = Path(__file__).parent.parent / "fixtures" / "ggi" / "list.html"

# NOTES.md에서 확인한 실제 행 하나:
EXPECTED_CASE_NO = "2024타경12345"  # <- 교체
EXPECTED_VIEWS = 1234               # <- 교체


def test_parse_ggi_list_extracts_rows():
    rows = parse_ggi_list(FIXTURE.read_text(encoding="utf-8"))
    assert len(rows) >= 1
    by_case = {c: r for c, r in rows}
    assert by_case[EXPECTED_CASE_NO].source is SourceName.GGI
    assert by_case[EXPECTED_CASE_NO].view_count == EXPECTED_VIEWS
```

- [ ] **Step 3: 실패 확인 후 구현** — `parse_ggi_list` 구현. Run: `uv run pytest tests/sources/test_parse_ggi.py -v` → PASS.

- [ ] **Step 4: 커밋**
```bash
git add src/auction_tracker/sources/parse/ggi.py tests/fixtures/ggi/ tests/sources/test_parse_ggi.py
git commit -m "feat: add ggi view-count list parser"
```

---

### Task 8: tank(탱크옥션) 조회수 파서

동일 패턴. **Files:** `src/auction_tracker/sources/parse/tank.py`, `tests/fixtures/tank/list.html`, `tests/fixtures/tank/NOTES.md`, `tests/sources/test_parse_tank.py`.
**Produces:** `parse_tank_list(html: str) -> list[tuple[str, ViewCountResult]]` (source=`TANK`).

- [ ] **Step 1: recon** — tankauction.com 목록 페이지 HTML을 `tests/fixtures/tank/list.html`로 저장 + NOTES.md 기록.
- [ ] **Step 2: 파싱 테스트 작성** — `tests/sources/test_parse_tank.py` (Task 7 구조와 동일하되 `parse_tank_list`, `SourceName.TANK`, NOTES.md 실제 값 사용)
```python
from pathlib import Path

from auction_tracker.sources.parse.tank import parse_tank_list
from auction_tracker.sources.types import SourceName

FIXTURE = Path(__file__).parent.parent / "fixtures" / "tank" / "list.html"
EXPECTED_CASE_NO = "2024타경12345"  # <- 교체
EXPECTED_VIEWS = 1000               # <- 교체


def test_parse_tank_list_extracts_rows():
    rows = parse_tank_list(FIXTURE.read_text(encoding="utf-8"))
    by_case = {c: r for c, r in rows}
    assert by_case[EXPECTED_CASE_NO].source is SourceName.TANK
    assert by_case[EXPECTED_CASE_NO].view_count == EXPECTED_VIEWS
```
- [ ] **Step 3: 실패 확인 후 구현** — `parse_tank_list`. Run: `uv run pytest tests/sources/test_parse_tank.py -v` → PASS.
- [ ] **Step 4: 커밋**
```bash
git add src/auction_tracker/sources/parse/tank.py tests/fixtures/tank/ tests/sources/test_parse_tank.py
git commit -m "feat: add tank view-count list parser"
```

---

### Task 9: dooin(두인경매) 조회수 파서

동일 패턴. **Files:** `src/auction_tracker/sources/parse/dooin.py`, `tests/fixtures/dooin/list.html`, `tests/fixtures/dooin/NOTES.md`, `tests/sources/test_parse_dooin.py`.
**Produces:** `parse_dooin_list(html: str) -> list[tuple[str, ViewCountResult]]` (source=`DOOIN`). 두인은 "조회수 랭킹" 페이지가 있으므로 그 페이지가 recon 대상으로 적합.

- [ ] **Step 1: recon** — dooinauction.com 조회수 랭킹/목록 페이지 HTML을 `tests/fixtures/dooin/list.html`로 저장 + NOTES.md 기록.
- [ ] **Step 2: 파싱 테스트 작성** — `tests/sources/test_parse_dooin.py`
```python
from pathlib import Path

from auction_tracker.sources.parse.dooin import parse_dooin_list
from auction_tracker.sources.types import SourceName

FIXTURE = Path(__file__).parent.parent / "fixtures" / "dooin" / "list.html"
EXPECTED_CASE_NO = "2024타경12345"  # <- 교체
EXPECTED_VIEWS = 500                # <- 교체


def test_parse_dooin_list_extracts_rows():
    rows = parse_dooin_list(FIXTURE.read_text(encoding="utf-8"))
    by_case = {c: r for c, r in rows}
    assert by_case[EXPECTED_CASE_NO].source is SourceName.DOOIN
    assert by_case[EXPECTED_CASE_NO].view_count == EXPECTED_VIEWS
```
- [ ] **Step 3: 실패 확인 후 구현** — `parse_dooin_list`. Run: `uv run pytest tests/sources/test_parse_dooin.py -v` → PASS.
- [ ] **Step 4: 커밋**
```bash
git add src/auction_tracker/sources/parse/dooin.py tests/fixtures/dooin/ tests/sources/test_parse_dooin.py
git commit -m "feat: add dooin view-count list parser"
```

---

### Task 10: 어댑터(페치+파싱 연결) — courtauction & ggi 대표 구현

> 5개 소스 어댑터는 구조가 동일하므로, 이 태스크에서 **facts 계열 1개(courtauction)** 와 **view-count 계열 1개(ggi)** 를 완성해 패턴을 확정한다. 나머지(onbid/tank/dooin) 어댑터는 동일 구조를 그대로 복제하되 각자의 파서·URL을 쓰며, 이 태스크의 마지막 스텝에서 함께 만든다.

**Files:**
- Create: `src/auction_tracker/sources/adapters/__init__.py`(빈 파일), `src/auction_tracker/sources/adapters/courtauction.py`, `src/auction_tracker/sources/adapters/ggi.py`, `src/auction_tracker/sources/adapters/onbid.py`, `src/auction_tracker/sources/adapters/tank.py`, `src/auction_tracker/sources/adapters/dooin.py`
- Test: `tests/sources/test_adapters.py`

**Interfaces:**
- Consumes: `sources.http_client.fetch`, `sources.parse.*`, `sources.types.*`, `sources.matching.pick_matching`, `sources.base` 프로토콜
- Produces:
  - `CourtAuctionAdapter(fetcher=..., limiter=...)` — `source=COURTAUCTION`, `fetch_facts(*, case_no, item_no=None, onbid_no=None) -> PropertyFacts | None`. `fetcher`는 `(url) -> str` 콜러블(기본은 `http_client.fetch`를 감싼 것). URL 구성 실패/파싱 전무 시 `None`, 네트워크 예외는 `SourceError`로 변환.
  - `GgiAdapter(fetcher=..., limiter=...)` — `source=GGI`, `fetch_view_count(*, case_no, item_no=None) -> ViewCountResult | None`. 목록을 페치→`parse_ggi_list`→`pick_matching(case_no, rows)`로 해당 물건 조회수 반환, 없으면 None.
  - 나머지 3개 어댑터도 동일 시그니처(onbid=facts, tank/dooin=view-count).
- **의존성 주입**: 어댑터 생성자는 `fetcher: Callable[[str], str]`를 받는다. 테스트는 저장된 픽스처 문자열을 반환하는 fake fetcher를 주입해 네트워크 없이 검증한다.

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/sources/test_adapters.py`
```python
from pathlib import Path

from auction_tracker.sources.adapters.courtauction import CourtAuctionAdapter
from auction_tracker.sources.adapters.ggi import GgiAdapter
from auction_tracker.sources.types import PropertyFacts, SourceName, ViewCountResult

FIX = Path(__file__).parent.parent / "fixtures"


def test_courtauction_adapter_returns_facts():
    html = (FIX / "courtauction" / "item.html").read_text(encoding="utf-8")
    adapter = CourtAuctionAdapter(fetcher=lambda url: html)
    facts = adapter.fetch_facts(case_no="2024타경12345", item_no="1")
    assert isinstance(facts, PropertyFacts)
    assert facts.source is SourceName.COURTAUCTION
    assert facts.appraisal_price is not None


def test_ggi_adapter_returns_view_count_for_matching_case():
    html = (FIX / "ggi" / "list.html").read_text(encoding="utf-8")
    adapter = GgiAdapter(fetcher=lambda url: html)
    # EXPECTED_CASE_NO는 tests/sources/test_parse_ggi.py와 동일한 recon 실제 값 사용
    from tests.sources.test_parse_ggi import EXPECTED_CASE_NO, EXPECTED_VIEWS

    res = adapter.fetch_view_count(case_no=EXPECTED_CASE_NO)
    assert isinstance(res, ViewCountResult)
    assert res.view_count == EXPECTED_VIEWS


def test_ggi_adapter_returns_none_for_unknown_case():
    html = (FIX / "ggi" / "list.html").read_text(encoding="utf-8")
    adapter = GgiAdapter(fetcher=lambda url: html)
    assert adapter.fetch_view_count(case_no="1999타경1") is None
```

- [ ] **Step 2: 실패 확인** — Run: `uv run pytest tests/sources/test_adapters.py -v` → FAIL (ModuleNotFoundError).

- [ ] **Step 3: courtauction 어댑터 구현** — `src/auction_tracker/sources/adapters/__init__.py`(빈 파일)과 `courtauction.py`:
```python
from typing import Callable, Optional

import httpx

from auction_tracker.sources.parse.courtauction import parse_courtauction_item
from auction_tracker.sources.types import PropertyFacts, SourceError, SourceName

# 실제 물건 상세 URL 템플릿은 recon(NOTES.md)에서 확인한 형식으로 채운다.
def _build_url(case_no: str, item_no: Optional[str]) -> str:
    # recon 기반: courtauction 물건 상세 URL 구성. NOTES.md의 실제 패턴 사용.
    raise NotImplementedError  # <- recon 후 실제 URL 구성으로 교체


class CourtAuctionAdapter:
    source = SourceName.COURTAUCTION

    def __init__(self, fetcher: Callable[[str], str]) -> None:
        self._fetcher = fetcher

    def fetch_facts(
        self, *, case_no: Optional[str] = None, item_no: Optional[str] = None, onbid_no: Optional[str] = None
    ) -> Optional[PropertyFacts]:
        if not case_no:
            return None
        url = _build_url(case_no, item_no)
        try:
            html = self._fetcher(url)
        except httpx.HTTPError as exc:
            raise SourceError(self.source, f"fetch failed: {exc}") from exc
        return parse_courtauction_item(html)
```
> 주의: `_build_url`은 recon으로 실제 URL 패턴을 확인해 구현한다. 어댑터 테스트는 `fetcher`를 주입하므로 URL이 실제로 호출되진 않지만, `_build_url`이 `NotImplementedError`를 던지면 테스트가 실패한다 → recon 값으로 채워야 통과. 만약 courtauction이 사건번호만으로 상세 URL을 직접 구성할 수 없고 검색을 거쳐야 하면, 어댑터를 "검색결과 목록 페치 → `pick_matching`" 방식으로 바꾸고 그 사실을 NOTES.md에 남긴다.

- [ ] **Step 4: ggi 어댑터 구현** — `src/auction_tracker/sources/adapters/ggi.py`:
```python
from typing import Callable, Optional

import httpx

from auction_tracker.sources.matching import pick_matching
from auction_tracker.sources.parse.ggi import parse_ggi_list
from auction_tracker.sources.types import SourceError, SourceName, ViewCountResult

def _build_list_url(case_no: str) -> str:
    # recon 기반: 사건번호로 조회 가능한 목록/검색 URL. NOTES.md 실제 패턴 사용.
    raise NotImplementedError  # <- recon 후 교체


class GgiAdapter:
    source = SourceName.GGI

    def __init__(self, fetcher: Callable[[str], str]) -> None:
        self._fetcher = fetcher

    def fetch_view_count(self, *, case_no: str, item_no: Optional[str] = None) -> Optional[ViewCountResult]:
        url = _build_list_url(case_no)
        try:
            html = self._fetcher(url)
        except httpx.HTTPError as exc:
            raise SourceError(self.source, f"fetch failed: {exc}") from exc
        rows = parse_ggi_list(html)
        return pick_matching(case_no, rows)
```

- [ ] **Step 5: 통과 확인(대표 2종)** — Run: `uv run pytest tests/sources/test_adapters.py -v` → PASS (3 passed).

- [ ] **Step 6: 나머지 3개 어댑터 복제 구현 + 테스트 확장** — `onbid.py`(facts, `parse_onbid_item`), `tank.py`(view-count, `parse_tank_list`), `dooin.py`(view-count, `parse_dooin_list`)를 위 두 패턴대로 작성. `tests/sources/test_adapters.py`에 각 어댑터가 픽스처 fake fetcher로 올바른 타입/값을 반환하는 테스트를 3개 추가(onbid=facts, tank/dooin=view-count, 각 recon 실제 값 사용). Run: `uv run pytest tests/sources/test_adapters.py -v` → PASS (6 passed).

- [ ] **Step 7: 커밋**
```bash
git add src/auction_tracker/sources/adapters/ tests/sources/test_adapters.py
git commit -m "feat: add source adapters wiring fetch and parse for all five sources"
```

---

### Task 11: 전체 스위트 & README 진행 갱신

**Files:**
- Modify: `README.md` (구현 진행 체크박스)
- Test: 전체 스위트

- [ ] **Step 1: 전체 테스트** — Run: `uv run pytest -v` → 모든 테스트 PASS (Plan 1 19개 + Plan 2a 신규). 실패 0.

- [ ] **Step 2: README 진행 갱신** — `README.md`의 "구현 진행" 섹션에서 Plan 2a 완료 표시를 추가:
```markdown
## 구현 진행
- [x] Plan 1: 기반 & 데이터 계층
- [x] Plan 2a: 소스 어댑터·파서·매칭
- [ ] Plan 2b: 크롤러 오케스트레이션 & 스케줄
- [ ] Plan 2c: 집계/점수 엔진 & 텔레그램 알림
- [ ] Plan 3: 웹 & 인증
```

- [ ] **Step 3: 커밋**
```bash
git add README.md
git commit -m "docs: mark Plan 2a complete in README"
```

---

## Self-Review (작성자 점검 결과)

**1. 스펙 커버리지 (Plan 2a 범위):**
- 소스 어댑터 플러그인 구조(스펙 4·어댑터) — Task 3(프로토콜)+Task 10(어댑터) ✅
- 5개 소스 파서(courtauction/onbid/ggi/tank/dooin) — Task 5·6·7·8·9 ✅
- 조회수 + 완료건 낙찰가율 추출(스펙 6·요구1) — `ViewCountResult.sale_ratio` 필드로 확보, view-count 파서에서 추출 ✅
- 사건번호 매칭(스펙 4·10, 정규화 재사용) — Task 4 ✅
- 저부하·재시도·UA(스펙 9) — Task 2 ✅
- 파싱/네트워크 분리로 오프라인 TDD(스펙 10 테스트 전략: 픽스처 파싱 단위테스트) — 전 파서 태스크 ✅
- Plan 2a 범위 밖(의도적): 스냅샷 저장·주기·비교군 수집·GitHub Actions → Plan 2b; 집계·점수·알림 → Plan 2c.

**2. 플레이스홀더 스캔:** 프레임워크 태스크(1~4)는 완전한 코드. 파서/어댑터 태스크의 `NotImplementedError`·`EXPECTED_*` 자리표시자는 **recon 픽스처 없이는 원천적으로 미리 알 수 없는 사이트 종속 값**이므로, 각 태스크의 recon 단계 산출물(NOTES.md 실제 값)로 채우도록 절차를 명시했다(정직한 제약, 임의 TODO 아님). 실사이트 구조가 예상과 다르면 NOTES.md에 기록하고 추출 계약을 조정하도록 대안 경로도 명시했다.

**3. 타입 일관성:** 반환 타입은 Task 1의 `PropertyFacts`/`ViewCountResult`로 고정. facts 파서→`PropertyFacts`, view-count 파서→`list[tuple[str, ViewCountResult]]`(매칭 입력 형태), 어댑터 시그니처는 Task 3 프로토콜과 일치(`fetch_facts`/`fetch_view_count`). `pick_matching` 입출력이 view-count 파서 반환형과 정합. ✅

**미결(2b/2c로 이월):** courtauction/onbid이 무세션으로 상세를 안 주거나 JS 렌더링이 필요하면 접근 범위 축소가 필요할 수 있음(recon에서 판정) — 2b 크롤러 설계 전에 확정.
