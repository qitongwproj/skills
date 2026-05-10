import html.parser


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


def parse_article(html_content):
    parser = ArticleParser()
    parser.feed(html_content)
    return {
        "title": parser.title.strip(),
        "author": parser.author.strip(),
        "content_html": parser.content_html,
    }