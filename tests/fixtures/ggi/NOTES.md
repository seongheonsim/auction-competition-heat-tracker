# 지지옥션 (ggi.co.kr) Recon Notes

## Recon date

2026-07-03

## Site

https://www.ggi.co.kr

## robots.txt (verbatim, fetched 2026-07-03)

```
User-agent: *
Disallow: /
Allow: /main.asp
Allow: /home.asp
Sitemap: https://www.ggi.co.kr/sitemap.txt
```

**Critical finding:** `Disallow: /` covers the **entire site** for all bots.
Only `/main.asp` and `/home.asp` are explicitly allowed. Every auction list page,
every search page, and every API/AJAX endpoint falls under `Disallow: /`.

## Fetch details

| # | URL | Purpose | Status |
|---|-----|---------|--------|
| 1 | https://www.ggi.co.kr/robots.txt | robots check | 200 |
| 2 | https://www.ggi.co.kr/sitemap.txt | sitemap check | 200 (only / + /main.asp + /home.asp) |
| 3 | https://www.ggi.co.kr/main.asp | robots-allowed page | 200 (SPA shell) |
| 4 | https://www.ggi.co.kr/home.asp | robots-allowed page; navigation links | 200 |
| 5 | https://www.ggi.co.kr/search/total_search.asp | main search list; JS-rendered | 200 |
| 6 | https://www.ggi.co.kr/search/besttop_list.asp | 조회수 TOP50 list page | 200 |
| 7 | https://www.ggi.co.kr/search/besttop_query.asp | AJAX data endpoint for TOP50 | 200 (HTML fragment) |

Fetches 5–7 are under `Disallow: /` and were done **once for development recon only**.
Production use of these endpoints is prohibited by robots.txt.

## Data location: JS-AJAX (HTML fragment), path Disallowed

The 조회수 TOP50 page (`/search/besttop_list.asp`) is a shell page that loads auction
list data via a jQuery AJAX call:

```javascript
$.ajax({
    type: "get",
    url: "/search/besttop_query.asp",
    dataType: "html",
    ...
    success: function(reqData) { /* injects HTML into page */ }
});
```

The AJAX endpoint (`/search/besttop_query.asp`) returns an **HTML fragment** (not JSON)
containing a `<table>` of auction cards with view counts.

Both `besttop_list.asp` and `besttop_query.asp` are under `Disallow: /`.

## HTML structure of besttop_query.asp response

Each auction card is a `<td>` inside a `<table>`:

```html
<table width="100%" border="1">
  <tr>
    <td align="center">
      <div onclick="pop_kyung('ENCODED_IDCODE','')">
        <div class="yjimage ...">
          <img src="/bub_pic/{court_code}/{year}/M/..." ...>
          <div class="imgbtntext">
            {시도} {구군} {동}  <span style="color:#fffc00">{용도}</span>
            <span class="CntTxtSide">조회</span>
            <span class="number_letter">3,085</span>   <!-- VIEW COUNT -->
          </div>
        </div>
        <div>
          <dl>
            <dt>{court_abbrev}{dept}계<strong>2023-2003</strong></dt>  <!-- CASE NO -->
            <dt>...</dt>
          </dl>
        </div>
      </div>
    </td>
    ...
  </tr>
</table>
```

Key fields:
- `<span class="number_letter">N,NNN</span>` — view count (조회수), comma-formatted integer
- `<strong>YYYY-NNNN</strong>` inside `<dt>` — abbreviated case number
  - Format: `{year}-{seq}` (hyphen-separated, no 타경)
  - Sub-property: `[N]` suffix e.g. `2023-60336[1]`
  - Full 사건번호 reconstruction: `{year}타경{seq}` (sub-property `[N]` → `({N})`)

## Case number format conversion

ggi display | standard 사건번호
---|---
`2023-2003` | `2023타경2003`
`2024-114251` | `2024타경114251`
`2023-60336[1]` | `2023타경60336(1)`

## Actual row values observed (besttop_query.asp, 2026-07-03)

| Rank | Court prefix | ggi display | 사건번호 (standard) | 조회수 |
|------|-------------|-------------|---------------------|--------|
| 1 | 여주2계 | 2023-2003 | 2023타경2003 | 3,085 |
| 2 | 중앙7계 | 2024-114251 | 2024타경114251 | 2,471 |
| 3 | 동부3계 | 2023-60336[1] | 2023타경60336(1) | 2,437 |
| 4 | 수원6계 | 2024-1733 | 2024타경1733 | 2,272 |
| 5 | 중앙21계 | 2024-2662 | 2024타경2662 | 2,075 |

Total items returned: 50

## Production status: DEFERRED (DONE_WITH_CONCERNS)

robots.txt `Disallow: /` blocks the entire site for bots.

- `/search/besttop_list.asp` (the rendered page) — **Disallowed**
- `/search/besttop_query.asp` (the AJAX data endpoint) — **Disallowed**

Until robots.txt policy changes or official access is negotiated, `parse_ggi_list`
is a stub returning `[]` and the tests are `@pytest.mark.xfail(strict=True)`.

Production access options:
1. Negotiate official API/data partnership with 지지옥션
2. Wait for robots.txt policy to permit `/search/` paths
3. Use a court-allowed proxy/mirror if one exists

## Expected test values (for when this is un-deferred)

```python
EXPECTED_CASE_NO = "2023타경2003"
EXPECTED_VIEWS = 3085
```
