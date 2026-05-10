import html.parser
import re


class HTML2Markdown(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.output = []
        self._buffer = ""
        self._list_stack = []
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
            if tag == "br":
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


def convert(html_content):
    converter = HTML2Markdown()
    converter.feed(html_content)
    return converter.get_markdown()