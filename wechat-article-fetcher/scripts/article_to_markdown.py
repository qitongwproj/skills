"""
将微信文章转换为 Markdown 格式
"""
import subprocess
import os
import re
from bs4 import BeautifulSoup
import html2text


# 配置 html2text
h2t = html2text.HTML2Text()
h2t.ignore_links = False
h2t.ignore_images = False
h2t.body_width = 0
h2t.unicode_snob = True


def fetch_article_html(url):
    """使用 curl 获取文章 HTML"""
    url = url.replace("#rd", "")
    cmd = [
        "curl.exe", "-s", "-k", "-L",
        "-o", "_tmp_article.html",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        url,
    ]
    subprocess.run(cmd, timeout=30)
    with open("_tmp_article.html", "r", encoding="utf-8") as f:
        return f.read()


def convert_to_markdown(html, url):
    """将 HTML 转换为 Markdown"""
    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("h1", id="activity-name")
    title = title.get_text(strip=True) if title else ""

    author = soup.find("span", id="js_name")
    author = author.get_text(strip=True) if author else ""

    content = soup.find("div", id="js_content")
    if content:
        markdown = h2t.handle(str(content))
        return f"# {title}\n\n作者: {author}\n\n---\n\n{markdown}"
    return None


def process_article(url, output_dir="articles"):
    """处理单篇文章"""
    os.makedirs(output_dir, exist_ok=True)

    html = fetch_article_html(url)
    markdown = convert_to_markdown(html, url)

    if markdown:
        # 生成文件名
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("h1", id="activity-name")
        title = title.get_text(strip=True) if title else "untitled"
        filename = re.sub(r'[\\/*?:"<>|]', "_", title) + ".md"

        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"原文链接: {url}\n\n{markdown}")

        print(f"已保存: {filepath}")
        return filepath

    return None


if __name__ == "__main__":
    # 示例：转换单篇文章
    URL = "https://mp.weixin.qq.com/s/xxxxx"
    process_article(URL)
