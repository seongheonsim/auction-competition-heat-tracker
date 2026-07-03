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
- [~] Plan 2a: 소스 어댑터·파서·매칭 (프레임워크 완료 / onbid·tank 구현 / courtauction·ggi·dooin 연기)
- [ ] Plan 2b: 크롤러 오케스트레이션 & 스케줄
- [ ] Plan 2c: 집계/점수 엔진 & 텔레그램 알림
- [ ] Plan 3: 웹 & 인증

## 소스 상태 (Plan 2a recon 결과)

| 소스 | 유형 | 상태 | 비고 |
|---|---|---|---|
| onbid (공매) | facts | ✅ 구현 | robots 없음(허용). JSON API. 프로덕션 fetch는 세션쿠키+CSRF 2단계 필요(Plan 2b). |
| tank (탱크옥션) | views | ⚠️ 파서만 구현 | 목록은 AJAX JSON. robots가 `/api` Disallow → 프로덕션 fetch는 헤드리스 브라우저 등 준수 경로 필요(Plan 2b). |
| courtauction (법원경매) | facts | ⛔ 연기 | WebSquare JS 프레임워크. 정적 fetch 불가 → 헤드리스 브라우저 필요. stub+xfail. |
| ggi (지지옥션) | views | ⛔ 연기 | robots `Disallow: /` (사이트 전체 차단). stub+xfail. |
| dooin (두인) | views | ⛔ 연기 | JS 렌더링 + robots `Disallow: /ca/`. stub+xfail. |

> 참고: 조회수(views) 소스 3곳(ggi·dooin) 및 courtauction은 robots.txt/JS 제약으로 프로덕션 정적 수집이 막혀 있다. 프로덕션 수집 전략(헤드리스 브라우저 채택 여부, robots/약관 준수, 공식 데이터 접근 협의)은 Plan 2b에서 결정해야 한다. 상세 recon 기록은 각 `tests/fixtures/<source>/NOTES.md` 참조.
