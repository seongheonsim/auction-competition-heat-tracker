# courtauction.go.kr Recon Notes

**Recon performed:** 2026-07-02

---

## robots.txt

- URL: `https://www.courtauction.go.kr/robots.txt`
- Result: **HTTP 404** — No robots.txt found on the server.
  The server returns the standard error HTML page (28,856 bytes) for this path.
- Conclusion: No explicit crawling restrictions stated. Responsible scraping still applies.

---

## Site Architecture

courtauction.go.kr uses the **WebSquare** framework (Korean enterprise web framework from Inswave Systems, inswave.com). WebSquare is an XHTML+XForms-like framework that:
- Delivers a thin HTML shell (~2,478 bytes) as the entry point for every `.on` URL
- Loads UI definitions as XML files (`.xml`)
- Makes all data requests as JSON POST calls from within the JavaScript runtime
- Requires the WebSquare runtime (websquare.js) to be running in a browser to function

---

## URLs Tried (in order)

| URL | Method | Status | Content-Type | Result |
|-----|--------|--------|--------------|--------|
| `https://www.courtauction.go.kr/robots.txt` | GET | 404 | text/html | 28,856-byte error page |
| `https://www.courtauction.go.kr/` | GET | 200 | text/html | 384-byte JS shell; redirects to `/pgj/index.on` via `window.location.href` |
| `https://www.courtauction.go.kr/pgj/index.on` | GET | 200 | text/html; charset=utf-8 | 2,478-byte WebSquare shell HTML (loads PGJ111M01.xml) |
| `https://www.courtauction.go.kr/pgj/ui/pgj100/PGJ111M01.xml` | GET | 200 | application/xml | 147,780-byte WebSquare XML UI definition (main real estate list page) |
| `https://www.courtauction.go.kr/pgj/ui/pgj100/PGJ151F00.xml` | GET | 200 | application/xml | 13,925-byte WebSquare XML UI definition (item detail search form) |
| `https://www.courtauction.go.kr/RetrieveRealEstateList.laf` | GET | 404 | text/html | 28,856-byte error page (old site URL pattern not found) |
| `https://www.courtauction.go.kr/pgj/pgj111/selectNtcMtrPouUpItemList.on` | POST JSON | 200 | text/html; charset=utf-8 | 2,478-byte WebSquare shell (request rejected, redirected to shell) |
| `https://www.courtauction.go.kr/pgj/pgj111/selectRletGdsList.on` | POST JSON | 200 | text/html; charset=utf-8 | 2,478-byte WebSquare shell |
| `https://www.courtauction.go.kr/pgj/pgj112/selectRletDtl.on` | POST JSON | 200 | text/html; charset=utf-8 | 2,478-byte WebSquare shell |
| `https://www.courtauction.go.kr/pgj/pgjsearch/searchControllerMain.on` | POST JSON `{}` | 500 | application/json;charset=UTF-8 | `{"errors":{"errorMessage":"에러…"}}` — endpoint accepts JSON but fails |
| `https://www.courtauction.go.kr/pgj/pgjsearch/searchControllerMain.on` | POST JSON `{"dma_pageInfo":{...},"dma_srchGdsDtlSrchInfo":{...}}` | 550 | application/json;charset=UTF-8 | `{"errors":{"errorMessage":"요청한 데이터가 없습니다."}}` — endpoint processes our format but returns 550 "no data" |
| `https://www.courtauction.go.kr/pgj/websquare/blank.xml` | GET | 200 | application/xml | 502-byte blank WebSquare XML |
| `https://www.courtauction.go.kr/pgj/websquare/websquare.js` | GET | 404 | text/html | WebSquare runtime JS not served (or CDN-hosted) |

---

## Key API Endpoint Discovered

From examining `PGJ151F00.xml` (item detail search form), the search submission uses:
- **URL**: `/pgj/pgjsearch/searchControllerMain.on`
- **Method**: POST
- **Content-Type**: `application/json`
- **Payload format (XForms ref)**: `data:json,["dma_pageInfo","dma_srchGdsDtlSrchInfo"]`
  - `dma_pageInfo`: `{pageNo, pageSize, totalYn, ...}`
  - `dma_srchGdsDtlSrchInfo`: `{bidDvsCd, mvprpRletDvsCd, cortAuctnSrchCondCd, aeeEvlAmtMin, aeeEvlAmtMax, ...}`

With a session cookie (JSESSIONID) and the format `{"dma_pageInfo":{...},"dma_srchGdsDtlSrchInfo":{...}}`, the endpoint returns HTTP 550 with `"요청한 데이터가 없습니다."` (The requested data does not exist) — which is progress over the generic 500 error, but still blocked.

---

## Why Static GET Fails

1. The server has a **security filter** that checks if requests come from within the WebSquare runtime (likely via a session token or CSRF-like mechanism set by the WebSquare JS initialization)
2. Without the WebSquare runtime running, all `.on` data endpoints return the 2,478-byte HTML shell instead of JSON data
3. The only exception is `/pgj/pgjsearch/searchControllerMain.on` which accepts JSON Content-Type but still requires a proper WebSquare session context

---

## Actual Values Read Off Live Pages

**None** — No parseable property data HTML could be obtained via static GET requests. The site requires JavaScript execution to render any auction item data.

---

## Alternative Approaches Required

To scrape courtauction.go.kr, one of the following approaches is needed:

### Option A: Playwright/Selenium (Recommended)
Use a headless browser (Playwright with `playwright install chromium`) to:
1. Load `https://www.courtauction.go.kr/pgj/index.on`
2. Wait for WebSquare to initialize
3. Navigate to the search page (PGJ151F00.xml frame)
4. Submit search form and intercept the XHR response from `searchControllerMain.on`
5. Parse the JSON response directly (no HTML parsing needed)

### Option B: WebSquare Session Reverse-Engineering
Capture an actual browser session using DevTools:
1. Open DevTools → Network tab
2. Load courtauction and perform a search
3. Copy the actual XHR request headers/payload to replicate the session token

### Option C: Open Data Portal (공공데이터포털)
Check if the Supreme Court provides courtauction data via the Korean Open Data Portal (data.go.kr). Search for "법원 경매" — this would be a REST API with an official API key, bypassing scraping entirely.

### Option D: Third-party Data Provider
Services like GoodAuction (goodauction.com) or Taekyung (takyung.com) aggregate courtauction data and may provide APIs.

---

## Status

**BLOCKED**: Static HTTP scraping of courtauction.go.kr is not feasible without a headless browser or official API access. The site is entirely WebSquare-rendered. PART B parser cannot be written without either (a) a Playwright-captured fixture or (b) a direct JSON response from the API.
