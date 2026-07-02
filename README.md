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
