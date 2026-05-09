import urllib.request
import urllib.error
import html.parser
import re
import os
import json
import sys

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "articles")


class WeChatArticleParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_target = False
        self.target_depth = 0
        self.current_depth = 0
        self.title = ""
        self.author = ""
        self.content_html = ""
        self._in_title = False
        self._in_author = False
        self._in_content = False
        self._content_depth = 0
        self._skip_tag = None

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


class HTML2Markdown(html.parser.HTMLParser):
    BLOCK_TAGS = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6",
                  "ul", "ol", "li", "blockquote", "pre", "hr", "table",
                  "section", "article", "header", "footer", "br"}
    INLINE_TAGS = {"a", "strong", "b", "em", "i", "code", "span", "img",
                   "sub", "sup", "del", "s", "u"}

    def __init__(self):
        super().__init__()
        self.output = []
        self._buffer = ""
        self._list_stack = []
        self._indent = 0
        self._ignore = 0
        self._pre = False
        self._pre_content = ""
        self._link_url = ""
        self._link_text = ""
        self._in_link = False
        self._in_img = False
        self._img_alt = ""
        self._img_src = ""
        self._skip_data = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if self._ignore > 0:
            self._ignore += 1
            return

        if tag in ("script", "style", "noscript"):
            self._ignore = 1
            return

        if self._pre:
            if tag == "pre":
                pass
            elif tag == "br":
                self._pre_content += "\n"
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._flush_buffer()
            level = int(tag[1])
            self._buffer = "#" * level + " "

        elif tag == "p":
            self._flush_buffer()

        elif tag == "br":
            self._flush_buffer()
            self.output.append("")

        elif tag == "hr":
            self._flush_buffer()
            self.output.append("---")
            self.output.append("")

        elif tag == "blockquote":
            self._flush_buffer()
            self._buffer = "> "

        elif tag == "pre":
            self._flush_buffer()
            self._pre = True
            self._pre_content = ""

        elif tag == "code":
            if not self._pre:
                self._buffer += "`"

        elif tag == "strong" or tag == "b":
            self._buffer += "**"

        elif tag == "em" or tag == "i":
            self._buffer += "*"

        elif tag == "del" or tag == "s":
            self._buffer += "~~"

        elif tag == "a":
            self._in_link = True
            self._link_url = attrs_dict.get("href", "")
            self._link_text = ""

        elif tag == "img":
            self._in_img = True
            self._img_alt = attrs_dict.get("alt", "")
            self._img_src = attrs_dict.get("src", attrs_dict.get("data-src", ""))

        elif tag == "ul":
            self._flush_buffer()
            self._list_stack.append("*")

        elif tag == "ol":
            self._flush_buffer()
            self._list_stack.append("1.")

        elif tag == "li":
            self._flush_buffer()
            prefix = self._list_stack[-1] if self._list_stack else "*"
            self._buffer = "  " * (len(self._list_stack) - 1) + prefix + " "

        elif tag == "table":
            self._flush_buffer()
            self._skip_data = True

        elif tag in ("div", "section", "article", "header", "footer", "span", "sub", "sup", "u"):
            pass

    def handle_endtag(self, tag):
        if self._ignore > 0:
            self._ignore -= 1
            return

        if self._pre:
            if tag == "pre":
                self._pre = False
                for line in self._pre_content.split("\n"):
                    self.output.append("    " + line)
                self.output.append("")
                self._pre_content = ""
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p"):
            self._flush_buffer()
            self.output.append("")

        elif tag == "blockquote":
            self._flush_buffer()
            self.output.append("")

        elif tag == "br":
            pass

        elif tag == "code":
            if not self._pre:
                self._buffer += "`"

        elif tag == "strong" or tag == "b":
            self._buffer += "**"

        elif tag == "em" or tag == "i":
            self._buffer += "*"

        elif tag == "del" or tag == "s":
            self._buffer += "~~"

        elif tag == "a":
            if self._in_link:
                self._in_link = False
                text = self._link_text.strip() if self._link_text else self._link_url
                if self._link_url and self._link_url != text:
                    self._buffer += f"[{text}]({self._link_url})"
                else:
                    self._buffer += text

        elif tag == "img":
            if self._in_img:
                self._in_img = False
                alt = self._img_alt or "图片"
                src = self._img_src or ""
                if src:
                    self._buffer += f"![{alt}]({src})"

        elif tag == "li":
            self._flush_buffer()

        elif tag in ("ul", "ol"):
            if self._list_stack:
                self._list_stack.pop()
            self._flush_buffer()
            self.output.append("")

        elif tag == "table":
            self._skip_data = False

        elif tag in ("div", "section", "article", "header", "footer", "span", "sub", "sup", "u"):
            pass

    def handle_data(self, data):
        if self._ignore > 0:
            return
        if self._skip_data:
            return

        if self._pre:
            self._pre_content += data
            return

        if self._in_link:
            self._link_text += data
            return

        text = data.replace("\n", " ").replace("\r", " ")
        text = re.sub(r"\s+", " ", text)
        self._buffer += text

    def handle_startendtag(self, tag, attrs):
        if tag == "br":
            self._flush_buffer()
            self.output.append("")
        elif tag == "hr":
            self._flush_buffer()
            self.output.append("---")
            self.output.append("")
        elif tag == "img":
            attrs_dict = dict(attrs)
            alt = attrs_dict.get("alt", "图片")
            src = attrs_dict.get("src", attrs_dict.get("data-src", ""))
            if src:
                self._buffer += f"![{alt}]({src})"

    def _flush_buffer(self):
        if self._buffer.strip():
            self.output.append(self._buffer.rstrip())
        self._buffer = ""

    def get_markdown(self):
        self._flush_buffer()
        return "\n".join(self.output).strip()


def fetch_html(url):
    url = url.replace("#rd", "").replace("http://", "https://")
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
                          "MicroMessenger/8.0.38"
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def convert_article(url):
    print(f"正在获取: {url}")
    html_content = fetch_html(url)

    parser = WeChatArticleParser()
    parser.feed(html_content)

    title = parser.title.strip()
    author = parser.author.strip()
    content_html = parser.content_html

    if not content_html:
        print(f"  警告: 未能提取文章内容")
        return None

    converter = HTML2Markdown()
    converter.feed(content_html)
    markdown_body = converter.get_markdown()

    safe_title = re.sub(r'[\\/*?:"<>|]', "_", title) if title else "untitled"
    filename = safe_title + ".md"

    full_md = f"# {title}\n\n**作者**: {author}\n\n**原文链接**: {url}\n\n---\n\n{markdown_body}"

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_md)

    print(f"  已保存: {filepath}")
    return filepath


def main():
    urls = [
        "https://mp.weixin.qq.com/s/rB_0TEbhOXECvI84ejlenw",
        "https://mp.weixin.qq.com/s/Zs-rAQjOLm0iLdfa34AkUg",
    ]

    for url in urls:
        try:
            convert_article(url)
        except Exception as e:
            print(f"  错误: {e}")

    print(f"\n完成！输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()