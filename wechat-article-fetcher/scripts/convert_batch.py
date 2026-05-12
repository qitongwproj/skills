import re
import os
import sys
import time

from fetch_html import fetch_html
from article_parser import parse_article
from html2md import convert as to_markdown

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "articles")


def convert_article(url):
    print(f"正在获取: {url}")
    html = fetch_html(url)

    article = parse_article(html)
    title = article["title"]
    author = article["author"]
    content_html = article["content_html"]

    if not content_html:
        print(f"  警告: 未能提取文章内容")
        return None

    markdown_body = to_markdown(content_html)

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
    if len(sys.argv) < 2:
        print("用法: python3 convert_batch.py <URL1> [URL2] ...")
        print("示例: python3 convert_batch.py https://mp.weixin.qq.com/s/xxxxx")
        sys.exit(1)

    urls = sys.argv[1:]

    for url in urls:
        try:
            convert_article(url)
            time.sleep(1)
        except Exception as e:
            print(f"  错误: {e}")

    print(f"\n完成！输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()