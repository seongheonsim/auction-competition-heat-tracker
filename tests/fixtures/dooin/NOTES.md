# Dooin Auction (두인경매) Recon Notes

## Fetch details

- **Recon date:** 2026-07-02
- **Site:** https://www.dooinauction.com
- **Target page:** https://www.dooinauction.com/ca/caTopView.php (조회수랭킹 — view-count ranking)

## robots.txt findings (verbatim)

Fetched: `https://www.dooinauction.com/robots.txt` → HTTP 200

```
User-agent: *
Allow:/
Allow:/res/main.php
Disallow:/member/
Disallow:/SOLAR/
Disallow:/doAdmin/
Disallow:/goAdmin/
Disallow:/res/
Disallow:/ca/
Disallow:ca/
Disallow:ca/caView.php
Disallow:ca/caFile.php
Disallow:/pa/
Disallow:pa/
Disallow:pa/paView.php
Disallow:pa/paFile.php
```

**Critical finding:** `Disallow: /ca/` — the entire `/ca/` subtree is disallowed for all bots.
This covers:
- `/ca/caTopView.php` (view-count ranking page) — **Disallowed**
- `/ca/caList.php` (main auction list) — **Disallowed**
- `/ca/res/topView.php` (JSON API endpoint for ranking data) — **Disallowed**

## Data location: HTML vs XHR/JSON

Fetched `/ca/caTopView.php` (HTTP 200). The page HTML contains:
```html
<ul id="rsList"></ul>
```
The list is **empty in static HTML**. Data is loaded via jQuery AJAX:

```javascript
// From /dist/ca/js/caTopView-CEHgfsLg.js
s.ajax({
  url: "/ca/res/topView.php",
  type: "POST",
  data: {mode: a, prd: prd, val: n},
  dataType: "JSON",
  success: function(d) { /* populates #rsList */ }
})
```

**Conclusion:** Data is served as JSON from POST `/ca/res/topView.php` — NOT in static HTML.

## API endpoint structure (development recon only)

**Endpoint:** `POST https://www.dooinauction.com/ca/res/topView.php`
**Parameters:** `mode=1&prd=1&val=0` (mode=1: 경매종류별, prd=1: 1주, val=0: 전체)
**Response:** JSON `{"items": [...]}` (HTTP 200, Content-Type: application/json; charset=UTF-8)

Each item contains:
- `sn` (string): 사건번호, format `"YYYY타경 NNNNNN"` (space between 타경 and number)
- `hit` (int): 조회수 (view count for current period)
- `totHit` (int): 누적조회수 (total/cumulative view count)
- `tid` (int): 두인 internal ticket ID
- `cat` (string): 물건종류 (property type)
- `adrs` (string): 주소
- `apsl_amt` (string): 감정가 (appraisal amount)
- `minb_amt` (string): 최저입찰가 (minimum bid amount)

## Actual values read from development recon (mode=1, prd=1, val=0, 2026-07-02)

| Rank | sn (사건번호)     | hit (조회수) | tid     |
|------|-------------------|-------------|---------|
| 1    | 2026타경 100495   | 279         | 2507293 |
| 2    | 2024타경 56220    | 227         | 2298450 |
| 3    | 2025타경 914      | 202         | 2382032 |
| 4    | 2025타경 2942     | 200         | 2457296 |
| 5    | 2025타경 59367    | 177         | 2489329 |

Total items returned: 30

Note: `sn` field contains a space before the case number (e.g., `"2026타경 100495"`).
A production parser should normalise this to `"2026타경100495"` (no space) to match
the standard 사건번호 format used elsewhere in auction_tracker.

## Production status: DEFERRED (DONE_WITH_CONCERNS)

`/ca/res/topView.php` is under `Disallow: /ca/` in robots.txt.
`/ca/caTopView.php` (the rendered page) is also Disallowed.

Production fetch options:
1. **Headless browser** rendering of `/ca/caTopView.php` — would avoid hitting the API
   endpoint directly, but the rendered page is itself Disallowed.
2. **Negotiate official access / API key** with 두인경매.
3. **Wait for robots.txt policy change** permitting the `/ca/` path.

Until one of the above is resolved, `parse_dooin_list` is a stub returning `[]`
and the test is `@pytest.mark.xfail(strict=True)`.

No production fixture file exists (fetching from Disallowed paths is prohibited).
