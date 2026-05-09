---
name: "wechat-article-fetcher"
description: "Fetches WeChat official account album articles and converts to Markdown. Invoke when user provides a WeChat album URL or wants to extract articles from mp.weixin.qq.com."
---

# WeChat Article Fetcher

Fetch articles from WeChat official account albums and convert to Markdown.


## Core Capabilities

1. **Extract article links** from WeChat album URLs
2. **Convert to Markdown** with proper formatting
3. **Batch processing** for entire albums or multiple single articles


## Quick Start: Convert Single Articles

Use `scripts/convert_batch.py` — pure Python stdlib, zero dependencies:

```bash
python3 scripts/convert_batch.py
```

Edit the `urls` list at the bottom of the script to add article URLs. Output goes to `./articles/`.


## Workflow (High Freedom)

### Step 1: Extract Album Parameters

From album URL:
```
https://mp.weixin.qq.com/mp/appmsgalbum?__biz=BIZ&action=getalbum&album_id=ALBUM_ID
```

Extract:
- `__biz`: Account identifier
- `album_id`: Album identifier

### Step 2: Fetch First Page (No Auth Required)

```
GET https://mp.weixin.qq.com/mp/appmsgalbum?__biz={biz}&action=getalbum&album_id={id}&f=json
```

Response structure:
```json
{
  "getalbum_resp": {
    "article_list": [{"msgid": "...", "title": "...", "url": "..."}],
    "continue_flag": "1"
  }
}
```

### Step 3: Capture Auth Parameters (mitmproxy)

**Setup:**
```bash
pip install mitmproxy
mitmdump -s scripts/mitm_capture.py -p 8080 --set block_global=false
```

**Capture parameters:**
- `appmsg_token`
- `key`
- `uin`
- `pass_ticket`

### Step 4: Fetch All Pages (With Auth)

Use `scripts/fetch_album.py` or custom implementation with:
- `begin_msgid` + `begin_itemidx=1` for pagination
- Include all auth parameters in URL

### Step 5: Convert to Markdown

Use `scripts/convert_batch.py` — pure Python stdlib, zero dependencies. Implements a complete
HTML→Markdown converter using only `urllib.request` + `html.parser`.


## Key Technical Details

| Aspect | Detail |
|--------|--------|
| **User-Agent** | Must use mobile WeChat UA (`MicroMessenger/8.0.38` on iPhone), otherwise returns verification page |
| **First page** | No authentication required |
| **Pagination** | Requires auth params (mitmproxy capture) |
| **Auth TTL** | Hours (re-capture when expired) |
| **Rate limit** | 1-2s interval between requests |
| **Content extraction** | `div#js_content` for article body, `h1#activity-name` for title |
| **Platform** | All scripts use Python stdlib (`urllib`) — fully cross-platform (Linux / macOS / Windows) |


## Troubleshooting

| Issue | Solution |
|-------|----------|
| "环境异常" / verification required | Use mobile WeChat User-Agent: `Mozilla/5.0 (iPhone; ...) MicroMessenger/8.0.38`. Desktop UAs are blocked. |
| Title only, no content | Client-side rendered; try alternative methods |
| Images not loading | WeChat CDN requires client environment |


## Scripts Reference

| Script | Purpose | Dependencies |
|--------|---------|-------------|
| `scripts/convert_batch.py` | Batch convert article URLs to Markdown | **None** (pure stdlib) |
| `scripts/fetch_album.py` | Batch fetch article links from album | **None** (pure stdlib) |
| `scripts/mitm_capture.py` | mitmproxy capture script for auth params | `mitmproxy` |


## Output Structure

```
./
├── article_links/     # Article URLs (JSON) — output to ../article_links/
├── articles/          # Markdown files — output to ../articles/
└── scripts/           # Helper scripts
```