---
name: "wechat-article-fetcher"
description: "Fetches WeChat official account album articles and converts to Markdown. Invoke when user provides a WeChat album URL or wants to extract articles from mp.weixin.qq.com."
---

# WeChat Article Fetcher

Fetch articles from WeChat official account albums and convert to Markdown.


## Core Capabilities

1. **Extract article links** from WeChat album URLs
2. **Convert to Markdown** with proper formatting
3. **Batch processing** for entire albums


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

Use `scripts/article_to_markdown.py` or:
```python
import html2text
from bs4 import BeautifulSoup

h2t = html2text.HTML2Text()
h2t.body_width = 0

soup = BeautifulSoup(html, "html.parser")
content = soup.find("div", id="js_content")
markdown = h2t.handle(str(content))
```


## Key Technical Details

| Aspect | Detail |
|--------|--------|
| **First page** | No authentication required |
| **Pagination** | Requires auth params (mitmproxy capture) |
| **Auth TTL** | Hours (re-capture when expired) |
| **Rate limit** | 1-2s interval between requests |
| **Content extraction** | `div#js_content` for article body |


## Troubleshooting

| Issue | Solution |
|-------|----------|
| "环境异常" / verification required | Use WebFetch tool or manual copy |
| Title only, no content | Client-side rendered; try alternative methods |
| Images not loading | WeChat CDN requires client environment |


## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/fetch_album.py` | Batch fetch article links |
| `scripts/article_to_markdown.py` | Convert HTML to Markdown |
| `scripts/mitm_capture.py` | mitmproxy capture script |


## Output Structure

```
./
├── article_links/     # Article URLs (JSON)
├── articles/          # Markdown files
└── scripts/           # Helper scripts
```
