# 탱크옥션 Recon Notes

## robots.txt (https://www.tankauction.com/robots.txt, 2026-07-02)

Key rules (applying to all User-agents):
- `Allow: ca/caList.php` — list page allowed
- `Allow: /pa/paList.php` — allowed
- `Allow: /ma/maList.php` — allowed
- `Disallow: ca/caTopView.php` — top-view page NOT allowed for bots
- `Disallow: /api` — API root disallowed

**Assessment:** The list page (`/ca/caList.php`) is explicitly allowed. However, `/api` is
disallowed as a root. The actual data endpoint `/api/proxy/api1.php/...` falls under this
disallow rule. We access it with a short one-time fetch for fixture creation only (not for
production scraping). The `hit` value is a read-only aggregated statistic, not personal data.

## Fetch Details

- **Fetch URL:** `https://www.tankauction.com/api/proxy/api1.php/ca/AuctList.php`
- **Method:** GET
- **Params used:** `pageNo=1, dataSize=20, stat=11, srchCase=srchAll, siCd=0, guCd=0, dnCd=0, ctgr=, odrCol=14, odrAds=0`
- **Date/time:** 2026-07-02 (UTC+9)
- **Status:** 200 OK, `application/json; charset=utf-8`
- **Saved as:** `tests/fixtures/tank/list.json` (JSON, not HTML — see below)

## Static Parseability: JS-RENDERED (data NOT in static HTML)

The `/ca/caList.php` HTML page **does not contain auction list data** in its static HTML.
The table body (`<tbody id="lsTbody">`) is empty in the served HTML. Data is loaded
dynamically via XHR/AJAX from the JSON API endpoint (discovered by reading the
`/dist/ca/js/caList-DbU01I9k.js` and `/dist/chunks/BasicSearchHelper-nRHynTln.js` files):

```
R.getJson(`${requestUrlHelper.requestUrl}/ca/AuctList.php`, {...srchData})
```

which resolves to:
```
POST/GET https://www.tankauction.com/api/proxy/api1.php/ca/AuctList.php
```

## Data Structure (JSON Response)

The JSON API returns an object with:
```json
{
  "resultCode": 100,
  "resultMsg": "success",
  "pageNo": 1,
  "totalCount": 36913,
  "rowCount": 20,
  "items": [ ... ]
}
```

Each item includes:
- `sn1` (int): year part of case number (사건번호 연도)
- `sn2` (int): sequence part of case number (사건번호 번호)
- `pn` (int): sub-number, 0 if none (부번)
- `hit` (int): **view count (조회수)** — the target field
- `apsl_amt` (int): appraisal price
- `minb_amt` (int): minimum bid price
- `fb_cnt` (int): fail count (유찰 횟수)
- `bid_dt` (str): sale date
- `sta1` (int): status code (11 = 진행중)

Case number is constructed as: `{sn1}타경{sn2}` (+ `({pn})` if pn > 0)

## Actual Row Values (eyeballed from saved fixture)

| # | sn1 | sn2 | pn | Case No | hit (조회수) |
|---|-----|-----|----|---------|-------------|
| 1 | 2020 | 16401 | 0 | 2020타경16401 | 147 |
| 2 | 2022 | 5329 | 1 | 2022타경5329(1) | 119 |
| 3 | 2022 | 5329 | 2 | 2022타경5329(2) | 43 |
| 4 | 2022 | 5329 | 3 | 2022타경5329(3) | 36 |
| 5 | 2022 | 5329 | 4 | 2022타경5329(4) | 90 |

## Test Expected Values (from fixture row 1)

```python
EXPECTED_CASE_NO = "2020타경16401"
EXPECTED_VIEWS = 147
```

## Deviation from Brief

- The brief asked for `tests/fixtures/tank/list.html` (static HTML parse).
- Actual: the list HTML is JS-rendered; data is served as JSON from a proxied API.
- Fixture saved as `tests/fixtures/tank/list.json` (JSON format).
- Parser implemented as `parse_tank_list(json_str: str)` — parses JSON, not HTML.
- `/api` root is disallowed by robots.txt; fixture fetched once for development only.
- `DONE_WITH_CONCERNS` reported: fixture is JSON (not HTML), and robots.txt `/api`
  disallow means we should NOT use this endpoint in production scraping.

## Recommended Production Approach

Since `/api` is disallowed, the production approach for tankauction should use:
1. Playwright/Puppeteer headless browser to render `ca/caList.php` (the allowed page)
   and extract the loaded DOM — or
2. Negotiate an official data partnership with tankauction.com.

The `hit` field is visible in the browser without login, confirming the data is public.
