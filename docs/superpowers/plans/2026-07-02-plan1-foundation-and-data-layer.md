# Plan 1 — 기반 & 데이터 계층 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 프로젝트 스캐폴딩·설정·DB 스키마(6개 테이블)·워치리스트 데이터 계층을 구축해, 경매 물건을 등록/조회/비활성화할 수 있는 검증된 데이터 계층을 만든다.

**Architecture:** Python 패키지(`auction_tracker`) 안에 설정(`config`)·DB 세션(`db`)·SQLAlchemy 모델(`models`)·리포지토리(`repositories/`)를 둔다. 프로덕션 DB는 Supabase(PostgreSQL)이지만, 단위테스트는 인메모리 SQLite로 빠르게 돈다(모델은 두 DB에 모두 호환되는 타입만 사용). 스키마 이관은 Alembic으로 관리한다.

**Tech Stack:** Python 3.12 · uv(패키지 관리) · SQLAlchemy 2.0(ORM) · Alembic(마이그레이션) · psycopg 3(Postgres 드라이버) · pydantic-settings(설정) · pytest(테스트).

## Global Constraints

- Python 버전: **3.12** (pyproject의 `requires-python = ">=3.12"`).
- 패키지 관리: **uv**. 의존성 추가는 `uv add <pkg>`, 테스트 실행은 `uv run pytest`.
- 소스 루트: **`src/auction_tracker/`** (src-layout). 테스트는 **`tests/`**.
- DB 이식성: 모델은 `sqlalchemy.JSON`·`BigInteger` 등 **SQLite/Postgres 공통 타입만** 사용(단위테스트를 SQLite로 돌리기 위함). Postgres 전용 타입 금지.
- 금액(원) 컬럼은 2^31을 초과할 수 있으므로 **`BigInteger`** 사용.
- 커밋 메시지는 Conventional Commits(`feat:`, `chore:`, `test:` 등) 사용.
- 시간대 인식: 타임스탬프 기본값은 `datetime.now(tz=timezone.utc)`(naive datetime 금지).

---

## File Structure

- `pyproject.toml` — 프로젝트 메타·의존성 (uv)
- `.env.example` — 필요한 환경변수 예시
- `.gitignore` — Python/uv 표준 무시 목록
- `src/auction_tracker/__init__.py` — 패키지 마커
- `src/auction_tracker/config.py` — pydantic-settings 기반 설정 로더
- `src/auction_tracker/db.py` — SQLAlchemy 엔진·세션 팩토리
- `src/auction_tracker/models.py` — 6개 테이블 ORM 모델 + `Base`
- `src/auction_tracker/normalize.py` — 사건번호 정규화 유틸
- `src/auction_tracker/repositories/__init__.py`
- `src/auction_tracker/repositories/watchlist.py` — 워치리스트 CRUD
- `alembic.ini`, `alembic/env.py`, `alembic/versions/*` — 마이그레이션
- `tests/conftest.py` — 인메모리 SQLite 세션 픽스처
- `tests/test_config.py`, `tests/test_normalize.py`, `tests/test_models.py`, `tests/test_watchlist_repo.py`

---

### Task 1: 프로젝트 스캐폴딩 & 설정 로더

**Files:**
- Create: `pyproject.toml`, `.env.example`, `.gitignore`, `src/auction_tracker/__init__.py`, `src/auction_tracker/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: (없음)
- Produces: `auction_tracker.config.Settings` (pydantic-settings 클래스), `auction_tracker.config.get_settings() -> Settings`. 필드: `database_url: str`, `app_password_hash: str = ""`, `session_secret: str = "dev-secret"`, `imminent_days: int = 5`.

- [ ] **Step 1: uv 프로젝트 초기화 및 의존성 추가**

Run:
```bash
cd "D:/personal/prediction-auction-bid-rates"
uv init --package --name auction-tracker --python 3.12 .
uv add sqlalchemy "psycopg[binary]" pydantic-settings alembic
uv add --dev pytest
```
Expected: `pyproject.toml`, `src/auction_tracker/` 생성, `uv.lock` 생성.

- [ ] **Step 2: `.gitignore`와 `.env.example` 작성**

`.gitignore`:
```
.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
```

`.env.example`:
```
# Supabase Postgres 연결 문자열 (psycopg 드라이버)
DATABASE_URL=postgresql+psycopg://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres
# 대시보드 단일 비밀번호의 해시(Plan 3에서 생성). 미설정이면 로그인 비활성.
APP_PASSWORD_HASH=
# 세션 쿠키 서명 키
SESSION_SECRET=change-me
# 개찰 임박 임계일수
IMMINENT_DAYS=5
```

- [ ] **Step 3: 실패하는 테스트 작성**

`tests/test_config.py`:
```python
from auction_tracker.config import Settings


def test_settings_reads_database_url_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h:5432/db")
    settings = Settings()
    assert settings.database_url == "postgresql+psycopg://u:p@h:5432/db"


def test_settings_defaults():
    settings = Settings(database_url="sqlite://")
    assert settings.imminent_days == 5
    assert settings.session_secret == "dev-secret"
```

- [ ] **Step 4: 테스트 실패 확인**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'auction_tracker.config'`

- [ ] **Step 5: `config.py` 구현**

`src/auction_tracker/config.py`:
```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    app_password_hash: str = ""
    session_secret: str = "dev-secret"
    imminent_days: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 6: 테스트 통과 확인**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS (2 passed)

- [ ] **Step 7: 커밋**

```bash
git add pyproject.toml uv.lock .gitignore .env.example src/auction_tracker/__init__.py src/auction_tracker/config.py tests/test_config.py
git commit -m "feat: scaffold project with uv and settings loader"
```

---

### Task 2: 사건번호 정규화 유틸

**Files:**
- Create: `src/auction_tracker/normalize.py`
- Test: `tests/test_normalize.py`

**Interfaces:**
- Consumes: (없음)
- Produces: `auction_tracker.normalize.normalize_case_no(raw: str) -> str`. 공백 제거, 전각→반각 아님, "타경" 앞뒤 공백/하이픈 정리, 대문자화 없음(한글). 예: `"2024 타경 12345"` → `"2024타경12345"`, `"2024타경-12345"` → `"2024타경12345"`.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_normalize.py`:
```python
import pytest

from auction_tracker.normalize import normalize_case_no


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2024타경12345", "2024타경12345"),
        ("2024 타경 12345", "2024타경12345"),
        (" 2024타경-12345 ", "2024타경12345"),
        ("2024\t타경\n12345", "2024타경12345"),
    ],
)
def test_normalize_case_no(raw, expected):
    assert normalize_case_no(raw) == expected


def test_normalize_case_no_rejects_empty():
    with pytest.raises(ValueError):
        normalize_case_no("   ")
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `uv run pytest tests/test_normalize.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'auction_tracker.normalize'`

- [ ] **Step 3: `normalize.py` 구현**

`src/auction_tracker/normalize.py`:
```python
import re

_WHITESPACE = re.compile(r"\s+")


def normalize_case_no(raw: str) -> str:
    """사건번호를 표준형으로 정규화한다. 예: '2024 타경 12345' -> '2024타경12345'."""
    if raw is None:
        raise ValueError("case_no is required")
    cleaned = _WHITESPACE.sub("", raw).replace("-", "")
    if not cleaned:
        raise ValueError("case_no is empty after normalization")
    return cleaned
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/test_normalize.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: 커밋**

```bash
git add src/auction_tracker/normalize.py tests/test_normalize.py
git commit -m "feat: add case number normalization util"
```

---

### Task 3: DB 세션 팩토리

**Files:**
- Create: `src/auction_tracker/db.py`, `tests/test_db_smoke.py`

> 주의(순서): `tests/conftest.py`(SQLite `session` 픽스처)는 `auction_tracker.models.Base`를 import하므로 **Task 4에서** 모델과 함께 생성한다. Task 3에서 conftest를 만들면 pytest가 어떤 테스트를 수집하든 conftest를 로드하다 ImportError로 실패한다.

**Interfaces:**
- Consumes: `auction_tracker.config.get_settings`
- Produces:
  - `auction_tracker.db.make_engine(url: str) -> Engine`
  - `auction_tracker.db.make_session_factory(engine) -> sessionmaker[Session]`

- [ ] **Step 1: `db.py` 구현 (엔진/세션 팩토리)**

`src/auction_tracker/db.py`:
```python
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def make_engine(url: str) -> Engine:
    return create_engine(url, future=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
```

- [ ] **Step 2: db 스모크 테스트 작성 및 실행**

`tests/test_db_smoke.py`:
```python
from sqlalchemy import text

from auction_tracker.db import make_engine, make_session_factory


def test_engine_executes_scalar():
    engine = make_engine("sqlite://")
    factory = make_session_factory(engine)
    with factory() as s:
        assert s.execute(text("select 1")).scalar_one() == 1
```

Run: `uv run pytest tests/test_db_smoke.py -v`
Expected: PASS (1 passed)

- [ ] **Step 3: 커밋**

```bash
git add src/auction_tracker/db.py tests/test_db_smoke.py
git commit -m "feat: add db engine/session factory"
```

---

### Task 4: ORM 모델 (6개 테이블)

**Files:**
- Create: `src/auction_tracker/models.py`, `tests/conftest.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: (없음)
- Produces: `auction_tracker.models.Base` 및 모델 클래스 `WatchlistItem`, `SourceLink`, `DailySnapshot`, `AuctionResult`, `ComparableCase`, `CompLink`. 필드는 스펙 섹션 5와 일치. `tests/conftest.py`의 `session` 픽스처(인메모리 SQLite, 각 테스트마다 새 스키마)도 이 태스크에서 생성 — 이후 모든 DB 테스트가 사용.

- [ ] **Step 1a: conftest 픽스처 작성**

`tests/conftest.py`:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from auction_tracker.models import Base


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite://", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    with factory() as s:
        yield s
    Base.metadata.drop_all(engine)
```

- [ ] **Step 1b: 실패하는 테스트 작성**

`tests/test_models.py`:
```python
import datetime as dt

from auction_tracker.models import (
    AuctionResult,
    ComparableCase,
    CompLink,
    DailySnapshot,
    SourceLink,
    WatchlistItem,
)


def test_insert_and_read_watchlist_item(session):
    item = WatchlistItem(
        source_type="court",
        case_no="2024타경12345",
        item_no="1",
        label="○○동 아파트",
    )
    session.add(item)
    session.commit()

    row = session.query(WatchlistItem).one()
    assert row.id is not None
    assert row.active is True
    assert row.added_at is not None


def test_daily_snapshot_stores_raw_json(session):
    item = WatchlistItem(source_type="court", case_no="2024타경1", label="x")
    session.add(item)
    session.commit()
    snap = DailySnapshot(
        watchlist_item_id=item.id,
        source="ggi",
        captured_on=dt.date(2026, 7, 2),
        view_count=123,
        raw={"foo": "bar"},
    )
    session.add(snap)
    session.commit()
    assert session.query(DailySnapshot).one().raw == {"foo": "bar"}


def test_auction_result_and_comparable_and_complink(session):
    comp = ComparableCase(
        source_type="court", case_no="2023타경9", property_type="아파트"
    )
    session.add(comp)
    session.commit()
    result = AuctionResult(
        comparable_case_id=comp.id,
        result_type="매각",
        sale_price=550_000_000,
        sale_ratio=0.91,
        result_date=dt.date(2026, 1, 10),
        source="courtauction",
    )
    session.add(result)
    session.commit()
    assert session.query(AuctionResult).one().sale_price == 550_000_000

    item = WatchlistItem(source_type="court", case_no="2024타경2", label="y")
    session.add(item)
    session.commit()
    link = CompLink(
        comparable_case_id=comp.id,
        watchlist_item_id=item.id,
        match_reason="same type + region",
    )
    session.add(link)
    session.commit()
    assert session.query(CompLink).one().match_reason == "same type + region"


def test_source_link(session):
    item = WatchlistItem(source_type="court", case_no="2024타경3", label="z")
    session.add(item)
    session.commit()
    sl = SourceLink(
        watchlist_item_id=item.id,
        source="ggi",
        external_id_or_url="https://www.ggi.co.kr/...",
        match_status="auto",
    )
    session.add(sl)
    session.commit()
    assert session.query(SourceLink).one().match_status == "auto"
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `uv run pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'auction_tracker.models'`

- [ ] **Step 3: `models.py` 구현**

`src/auction_tracker/models.py`:
```python
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
```

- [ ] **Step 4: 테스트 통과 확인 (모델 + conftest 픽스처)**

Run: `uv run pytest tests/test_models.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: 커밋**

```bash
git add src/auction_tracker/models.py tests/conftest.py tests/test_models.py
git commit -m "feat: add ORM models for all six tables and sqlite session fixture"
```

---

### Task 5: 워치리스트 리포지토리

**Files:**
- Create: `src/auction_tracker/repositories/__init__.py`, `src/auction_tracker/repositories/watchlist.py`
- Test: `tests/test_watchlist_repo.py`

**Interfaces:**
- Consumes: `auction_tracker.models.WatchlistItem`, `auction_tracker.normalize.normalize_case_no`, SQLAlchemy `Session`
- Produces (모두 `session: Session`을 첫 인자로 받음):
  - `add_court_item(session, *, case_no: str, item_no: str | None, label: str, region=None, property_type=None) -> WatchlistItem` — case_no는 정규화 후 저장, 동일 (case_no, item_no) 중복 시 `ValueError`.
  - `add_onbid_item(session, *, onbid_no: str, label: str, region=None, property_type=None) -> WatchlistItem`
  - `list_active(session) -> list[WatchlistItem]` — active=True만, added_at 오름차순.
  - `get(session, item_id: int) -> WatchlistItem | None`
  - `deactivate(session, item_id: int) -> bool` — 있으면 active=False로, 성공 True.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_watchlist_repo.py`:
```python
import pytest

from auction_tracker.repositories import watchlist as repo


def test_add_court_item_normalizes_case_no(session):
    item = repo.add_court_item(
        session, case_no="2024 타경 12345", item_no="1", label="아파트 A"
    )
    assert item.case_no == "2024타경12345"
    assert item.source_type == "court"
    assert item.active is True


def test_add_court_item_rejects_duplicate(session):
    repo.add_court_item(session, case_no="2024타경1", item_no="1", label="A")
    with pytest.raises(ValueError):
        repo.add_court_item(session, case_no="2024 타경 1", item_no="1", label="A dup")


def test_add_onbid_item(session):
    item = repo.add_onbid_item(session, onbid_no="2024-01234-001", label="공매 B")
    assert item.source_type == "onbid"
    assert item.onbid_no == "2024-01234-001"


def test_list_active_excludes_deactivated(session):
    a = repo.add_court_item(session, case_no="2024타경1", item_no="1", label="A")
    b = repo.add_court_item(session, case_no="2024타경2", item_no="1", label="B")
    assert repo.deactivate(session, a.id) is True
    active = repo.list_active(session)
    assert [i.id for i in active] == [b.id]


def test_get_returns_none_for_missing(session):
    assert repo.get(session, 999) is None


def test_deactivate_missing_returns_false(session):
    assert repo.deactivate(session, 999) is False
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `uv run pytest tests/test_watchlist_repo.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'auction_tracker.repositories'`

- [ ] **Step 3: 리포지토리 구현**

`src/auction_tracker/repositories/__init__.py`:
```python
```
(빈 파일 — 패키지 마커)

`src/auction_tracker/repositories/watchlist.py`:
```python
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
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/test_watchlist_repo.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: 커밋**

```bash
git add src/auction_tracker/repositories/ tests/test_watchlist_repo.py
git commit -m "feat: add watchlist repository (add/list/get/deactivate)"
```

---

### Task 6: Alembic 마이그레이션 초기화

**Files:**
- Create: `alembic.ini`, `alembic/env.py`, `alembic/versions/<rev>_initial.py`
- Test: `tests/test_migration.py`

**Interfaces:**
- Consumes: `auction_tracker.models.Base`, `auction_tracker.config.get_settings`
- Produces: `alembic upgrade head`로 6개 테이블을 생성하는 초기 마이그레이션. 자동생성.

- [ ] **Step 1: Alembic 초기화**

Run:
```bash
uv run alembic init alembic
```
Expected: `alembic.ini`, `alembic/env.py`, `alembic/versions/` 생성.

- [ ] **Step 2: `alembic/env.py`가 우리 설정·모델을 쓰도록 수정**

`alembic/env.py`의 상단 import 구역에 추가하고, `target_metadata`와 URL을 아래처럼 설정:
```python
from auction_tracker.config import get_settings
from auction_tracker.models import Base

target_metadata = Base.metadata
```
그리고 `config.get_main_option("sqlalchemy.url")`을 쓰는 대신, 오프라인/온라인 모두 URL을 설정에서 가져오도록 두 함수 시작부에 삽입:
```python
db_url = get_settings().database_url
config.set_main_option("sqlalchemy.url", db_url)
```
(`config`는 env.py에 이미 정의된 Alembic `Config` 객체다.)

- [ ] **Step 3: 초기 마이그레이션 자동생성**

Run (SQLite 임시 파일로 자동생성 — Postgres 접속 없이 스키마만 생성):
```bash
DATABASE_URL="sqlite:///./_tmp_autogen.db" uv run alembic revision --autogenerate -m "initial schema"
rm -f ./_tmp_autogen.db
```
Expected: `alembic/versions/<rev>_initial_schema.py` 생성, `op.create_table("watchlist_items", ...)` 등 6개 테이블 포함.

> Windows PowerShell에서는: `$env:DATABASE_URL="sqlite:///./_tmp_autogen.db"; uv run alembic revision --autogenerate -m "initial schema"; Remove-Item ./_tmp_autogen.db`

- [ ] **Step 4: 마이그레이션 적용 테스트 작성**

`tests/test_migration.py`:
```python
import subprocess
import sys


def test_alembic_upgrade_head_creates_tables(tmp_path):
    db_file = tmp_path / "mig.db"
    env = {"DATABASE_URL": f"sqlite:///{db_file}"}
    import os

    full_env = {**os.environ, **env}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        env=full_env,
    )
    assert result.returncode == 0, result.stderr

    from sqlalchemy import create_engine, inspect

    engine = create_engine(f"sqlite:///{db_file}")
    tables = set(inspect(engine).get_table_names())
    assert {
        "watchlist_items",
        "source_links",
        "daily_snapshots",
        "auction_results",
        "comparable_cases",
        "comp_links",
    }.issubset(tables)
```

- [ ] **Step 5: 테스트 실행**

Run: `uv run pytest tests/test_migration.py -v`
Expected: PASS (1 passed)

- [ ] **Step 6: 커밋**

```bash
git add alembic.ini alembic/ tests/test_migration.py
git commit -m "feat: add alembic initial migration for schema"
```

---

### Task 7: 전체 테스트 통과 & README 초안

**Files:**
- Create: `README.md`
- Test: 전체 스위트

- [ ] **Step 1: 전체 테스트 실행**

Run: `uv run pytest -v`
Expected: PASS (모든 테스트, 실패 0)

- [ ] **Step 2: README 작성**

`README.md`:
```markdown
# 경매 경쟁열기 추적·비교분석 도구

법원경매/공매 물건의 조회수 추세와 유사 사건 매각결과를 집계해 입찰 판단을 돕는 개인용 도구.
설계: `docs/superpowers/specs/2026-07-02-auction-competition-heat-tracker-design.md`

## 개발 셋업
- Python 3.12 + uv
- `uv sync` 로 의존성 설치
- `cp .env.example .env` 후 `DATABASE_URL`(Supabase) 입력
- 테스트: `uv run pytest`
- 마이그레이션 적용: `uv run alembic upgrade head`

## 구현 진행
- [x] Plan 1: 기반 & 데이터 계층
- [ ] Plan 2: 수집 파이프라인 (어댑터·크롤러·집계)
- [ ] Plan 3: 웹 & 인증
```

- [ ] **Step 3: 커밋**

```bash
git add README.md
git commit -m "docs: add README with setup and progress"
```

---

## Self-Review (작성자 점검 결과)

**1. 스펙 커버리지 (Plan 1 범위):**
- 스택(FastAPI 제외한 기반) — Task 1 ✅ / 사건번호 정규화(스펙 4·10) — Task 2 ✅ / DB 세션(Supabase Postgres, SQLite 테스트) — Task 3 ✅ / 6개 테이블 모델(스펙 5) — Task 4 ✅ / 워치리스트 CRUD(요구 4·데이터모델) — Task 5 ✅ / 마이그레이션 — Task 6 ✅.
- Plan 1 범위 밖(의도적): 어댑터·크롤러·적응형 주기·점수·비교분석·웹·인증 → Plan 2·3.

**2. 플레이스홀더 스캔:** "TBD/TODO/적절히 처리" 없음. 모든 코드 스텝에 실제 코드 포함. ✅

**3. 타입 일관성:** 리포지토리 시그니처(`add_court_item`/`list_active`/`deactivate`)가 Task 5 테스트와 일치. 모델 필드명이 Task 3 conftest·Task 4 테스트와 일치(`raw`, `captured_on`, `sale_ratio` 등). `JSON` 타입으로 SQLite/Postgres 공통. ✅
