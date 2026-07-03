# onbid.co.kr 공매 물건 파서 Recon Notes

## 조사 일시
2026-07-03

## robots.txt
```
HTTP 404 — www.onbid.co.kr/robots.txt 파일 없음
```
robots.txt가 존재하지 않으므로 RFC 9309 관례상 모든 경로가 크롤러에 허용됨.
단, `<meta name="robots" content="noindex, nofollow">` 태그가 로그인 페이지 HTML에
주석 처리(commented-out)된 상태로 존재함 — 실질적 의미 없음.

## 홈페이지 구조
- `https://www.onbid.co.kr/` → 200 OK, JavaScript로 즉시 로그인 페이지 리다이렉트:
  ```javascript
  window.location.replace("https://www.onbid.co.kr/op/meminf/lgnmng/prtllgn/PrtlLgnController/main.do");
  ```
- 사이트 전체가 Spring MVC + jQuery SPA (싱글 페이지 앱) 구조
- 모든 내비게이션 링크는 `javascript:void(0)` — 정적 HTML 링크 없음

## 데이터 위치
**XHR/JSON** — 정적 HTML 아님.
- 목록 API: `POST /op/cltrpbancinf/clbtcltrclg/prptclbtcltrclg/PrptClbtCltrController/inqOrgCltrClg.do`
  - 일반재산(국유지 등) 물건 목록 반환 (JSON)
- 유사 엔드포인트:
  - `inqCltrClbtRlstClg.do` — 부동산
  - `inqCltrClbtMvastClg.do` — 동산
  - `inqCltrClbtVhcClg.do` — 차량

## 접근 방법
실제 로그인(아이디/비밀번호) 없이 접근 가능.
단, 로그인 페이지를 먼저 방문해 세션 쿠키(`JSESSIONIDOP`) 및 CSRF 토큰을 획득해야 함:
1. `GET /op/meminf/lgnmng/prtllgn/PrtlLgnController/main.do` → 세션 쿠키 + CSRF 토큰
2. 검색 페이지 방문: `GET /op/cltrpbancinf/cltr/cltrcdtnsrch/CltrCdtnSrchController/mvmnCltrCdtnSrchClg.do`
3. 목록 API 호출 (POST, XHR 헤더 + X-CSRF-TOKEN 포함)

상세 페이지 (`/op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do`) 는
모든 파라미터 시도에서 HTTP 500 반환 — 실제 인증 필요로 추정.

## 인코딩
Response Content-Type: `text/html;charset=UTF-8`
실제 본문도 UTF-8 (Windows PowerShell 터미널 표시 문제로 인해 한국어가 깨져 보였으나
파일로 저장 시 정상 UTF-8).

## 물건관리번호 (scrnIndctCltrMngNo) 체계
형식: `YYYY-MMNN-NNNNNN`
예시: `2026-0600-033681`
- `2026` = 공고 연도
- `0600` = 공고 월/회차 코드 (06월 00번째 차)
- `033681` = 물건 일련번호

내부 `onbidCltrno`는 별도의 숫자형 ID (예: `2027800`).

## 픽스처 물건 정보
파일: `tests/fixtures/onbid/item.json`
물건명: 경상북도 김천시 율곡동 811 103호 근린생활시설
scrnIndctCltrMngNo: `2026-0600-033681`
onbidCltrno: `2027800`
카테고리: 상가용및업무용건물 / 근린생활시설
등록기관: 새김천새마을금고

## 픽스처에서 읽은 실제 값 (EXPECTED_*)

| 필드 | JSON 키 | 값 |
|------|---------|-----|
| appraisal_price | cltrApslEvlAvgAmt | 644,000,000 |
| min_price | lowstBidPrc | 381,000,000 |
| fail_count | uscbdCnt | 5 (문자열 "5" → int) |
| status | pbancPbctCltrStatNm | 입찰진행중 |
| sale_date | pbctDdlnDt | 2026-07-03 16:00 → date(2026, 7, 3) |
| result_type | (없음) | None |
| sale_price | (없음) | None |
| result_date | (없음) | None |

## 필드 노트

### cltrApslEvlAvgAmt (감정평가평균금액)
- 일부 물건에서 0으로 표시됨 — "미설정" 의미로 추정 → None 처리
- 다수의 물건에서 정상 금액 존재 (예: 644,000,000원)

### uscbdCnt (유찰횟수)
- 문자열 타입: "5"
- 이 물건의 누적 유찰 횟수로 추정
- `pbctNsq` (현재 공고 내 입찰 차수): "2" — 현재 공고에서 2번째 입찰 시도
- uscbdCnt와 pbctNsq가 불일치하는 경우 있음 (uscbdCnt = 누적 전체, pbctNsq = 현재 공고 내)

### pbctDdlnDt (입찰마감일시)
- sale_date 매핑: 입찰이 마감되는 날짜 = 사실상 공매 실시일
- 형식: "2026-07-03 16:00" → parse_kdate → date(2026, 7, 3)

### 결과(종료) 필드
- 목록 API에서 종료된 물건의 낙찰가(result/sale_price) 등은 별도 엔드포인트에서 제공
  (`/op/cltrpbancinf/bidrsltmng/cltrbidrslt/CltrBidRsltController/mvmnCltrBidRsltClg.do`)
- 현재 픽스처는 "입찰진행중" 물건이므로 result 필드 모두 None

## 상세 페이지 접근 한계
- `GET /op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do?onbidCltrno=2027800` → 500
- 시도한 모든 파라미터 조합에서 500 반환
- 상세 페이지에서만 얻을 수 있는 데이터 (개별 감정평가금액, 세부 유찰 이력 등) 는
  현재 미접근 상태

## 프로덕션 사용 고려사항
1. 세션 쿠키 갱신 주기 (JSESSIONIDOP) — 장기 실행 시 재획득 필요
2. X-CSRF-TOKEN 갱신 필요
3. robots.txt 없음 → 법적으로 허용되나, 서비스 약관 확인 권장
4. 목록 API는 최대 pageUnit 개수 제한이 있을 수 있음
