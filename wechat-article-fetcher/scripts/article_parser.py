import html
import html.parser
import re


class ArticleParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.author = ""
        self.content_html = ""
        self._in_title = False
        self._in_author = False
        self._in_content = False
        self._content_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "h1" and attrs_dict.get("id") == "activity-name":
            self._in_title = True
            return

        if tag == "span" and attrs_dict.get("id") == "js_name":
            self._in_author = True
            return

        if tag == "div" and attrs_dict.get("id") == "js_content":
            self._in_content = True
            self._content_depth = 1
            return

        if self._in_content:
            self._content_depth += 1
            attr_str = ""
            for k, v in attrs:
                if v is None:
                    attr_str += f" {k}"
                else:
                    attr_str += f' {k}="{v}"'
            self.content_html += f"<{tag}{attr_str}>"

    def handle_endtag(self, tag):
        if self._in_title and tag == "h1":
            self._in_title = False
            return

        if self._in_author and tag == "span":
            self._in_author = False
            return

        if self._in_content:
            self._content_depth -= 1
            if self._content_depth == 0:
                self._in_content = False
                return
            self.content_html += f"</{tag}>"

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif self._in_author:
            self.author += data
        elif self._in_content:
            self.content_html += data

    def handle_startendtag(self, tag, attrs):
        if self._in_content:
            attr_str = ""
            for k, v in attrs:
                if v is None:
                    attr_str += f" {k}"
                else:
                    attr_str += f' {k}="{v}"'
            self.content_html += f"<{tag}{attr_str}/>"


def _parse_new_format(html_content):
    og_match = re.search(r'og:title"\s*content="([^"]+)', html_content)
    if not og_match or len(og_match.group(1)) < 20:
        return None

    raw_text = html.unescape(og_match.group(1))
    raw_text = raw_text.replace('\\n', '\n')
    first_sentence = raw_text.split('。')[0].split('\n\n')[0].strip()
    title = first_sentence[:50] if first_sentence else "未知标题"

    author_match = re.search(r'og:article:author"\s*content="([^"]+)', html_content)
    author = html.unescape(author_match.group(1)) if author_match else "未知作者"

    paragraphs = [p.strip() for p in raw_text.split('\n\n') if p.strip()]
    content_html = "<p>" + "</p><p>".join(p.replace('\n', '<br/>') for p in paragraphs) + "</p>"

    return {
        "title": title,
        "author": author,
        "content_html": content_html,
    }


def parse_article(html_content):
    parser = ArticleParser()
    parser.feed(html_content)

    if parser.content_html.strip():
        return {
            "title": parser.title.strip() or "未知标题",
            "author": parser.author.strip() or "未知作者",
            "content_html": parser.content_html,
        }

    fallback = _parse_new_format(html_content)
    if fallback:
        return fallback

    return {
        "title": "",
        "author": "",
        "content_html": "",
    }