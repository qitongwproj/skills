---
name: "wechat-article-fetcher"
description: "Fetch WeChat official account articles (微信公众号文章) from mp.weixin.qq.com and convert to Markdown. Use this skill whenever the user provides a WeChat article URL, wants to extract or save WeChat articles, mentions 微信文章 or 公众号文章, needs to batch download articles from a WeChat album, or wants to parse WeChat article content into structured text. Supports individual article URLs and album URLs. All modules are independent — fetch HTML, parse content, and convert to Markdown can be used separately."
---

# WeChat Article Fetcher

Fetch articles from WeChat official account albums and convert to Markdown.


## Core Capabilities

1. **Extract article links** from WeChat album URLs → `fetch_album.py`
2. **Fetch article HTML** → `fetch_html.py`
3. **Parse article structure** (title, author, body) → `article_parser.py`
4. **Convert HTML to Markdown** → `html2md.py`
5. **Batch processing** (full pipeline) → `convert_batch.py`

All modules are independent — use only what you need.


## Quick Start: Convert Single Articles

```bash
python3 scripts/convert_batch.py <URL>
```

Supports multiple URLs at once:
```bash
python3 scripts/convert_batch.py URL1 URL2 URL3
```

Output goes to `../articles/`.

### Use Individual Modules

```python
from fetch_html import fetch_html
from article_parser import parse_article
from html2md import convert as to_markdown

html = fetch_html(url)              # Step 1: fetch
article = parse_article(html)       # Step 2: parse (title, author, content_html)
md = to_markdown(article["content_html"])  # Step 3: convert (optional)
```


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

Use `scripts/convert_batch.py` for the full pipeline, or compose individual modules:

```python
from fetch_html import fetch_html
from article_parser import parse_article
from html2md import convert as to_markdown

html = fetch_html(url)
article = parse_article(html)
md = to_markdown(article["content_html"])
```


## Key Technical Details

| Aspect | Detail |
|--------|--------|
| **User-Agent** | Must use mobile WeChat UA (`MicroMessenger/8.0.38` on iPhone), otherwise returns verification page |
| **First page** | No authentication required |
| **Pagination** | Requires auth params (mitmproxy capture) |
| **Auth TTL** | Hours (re-capture when expired) |
| **Rate limit** | 1-2s interval between requests |
| **Content extraction** | Primary: `div#js_content` for body, `h1#activity-name` for title. Fallback: `og:title` meta tag (for new-format pages where content is JS-rendered) |
| **Platform** | All scripts use Python stdlib (`urllib`) — fully cross-platform (Linux / macOS / Windows) |


## Troubleshooting

| Issue | Solution |
|-------|----------|
| "环境异常" / verification required | Use mobile WeChat User-Agent: `Mozilla/5.0 (iPhone; ...) MicroMessenger/8.0.38`. Desktop UAs are blocked. |
| Title only, no content | Parser auto-falls back to `og:title` meta tag for new-format pages (JS-rendered content). If still fails, the page may require client-side execution |
| Images not loading | WeChat CDN requires client environment |


## Scripts Reference

| Script | Purpose | Dependencies |
|--------|---------|-------------|
| `scripts/fetch_html.py` | Fetch raw HTML from article URL | **None** (pure stdlib) |
| `scripts/article_parser.py` | Parse article: title, author, content HTML. Supports both legacy (`div#js_content`) and new-format (`og:title` meta) WeChat pages | **None** (pure stdlib) |
| `scripts/html2md.py` | Convert HTML content to Markdown | **None** (pure stdlib) |
| `scripts/convert_batch.py` | Orchestrate fetch → parse → convert → save | **None** (pure stdlib) |
| `scripts/fetch_album.py` | Batch fetch article links from album | **None** (pure stdlib) |
| `scripts/mitm_capture.py` | mitmproxy capture script for auth params | `mitmproxy` |