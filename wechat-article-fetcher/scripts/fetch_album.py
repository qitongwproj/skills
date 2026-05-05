"""
批量获取微信公众号专辑文章链接
"""
import subprocess
import json
import os
import time


def fetch_album_articles(biz, album_id, auth_params=None):
    """
    获取专辑全部文章链接

    Args:
        biz: 公众号唯一标识
        album_id: 专辑ID
        auth_params: 认证参数字典（包含 appmsg_token, uin, key, pass_ticket）

    Returns:
        list: 文章列表，每项包含 title, url, mid
    """
    all_articles = []
    begin_msgid = ""
    page = 0

    while True:
        page += 1

        if begin_msgid and auth_params:
            # 翻页请求（需要认证参数）
            url = (
                f"https://mp.weixin.qq.com/mp/appmsgalbum?action=getalbum"
                f"&__biz={biz}&album_id={album_id}&count=10"
                f"&begin_msgid={begin_msgid}&begin_itemidx=1"
                f"&uin={auth_params['uin']}&key={auth_params['key']}"
                f"&pass_ticket={auth_params['pass_ticket']}&wxtoken="
                f"&devicetype=UnifiedPCWindows&clientversion=f254186b"
                f"&appmsg_token={auth_params['appmsg_token']}&x5=0&f=json"
            )
        else:
            # 第一页（无需认证）
            url = f"https://mp.weixin.qq.com/mp/appmsgalbum?__biz={biz}&action=getalbum&album_id={album_id}&f=json"

        # 使用 curl 获取
        tmp_file = "_tmp_resp.json"
        subprocess.run(["curl.exe", "-s", "-k", "-o", tmp_file, url], timeout=30)

        with open(tmp_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        articles = data.get("getalbum_resp", {}).get("article_list", [])
        continue_flag = data.get("getalbum_resp", {}).get("continue_flag", "0")

        for article in articles:
            all_articles.append({
                "title": article["title"].split("\n")[0],
                "url": article["url"].replace("http://", "https://"),
                "mid": article["msgid"]
            })
            begin_msgid = article["msgid"]

        if continue_flag != "1":
            break

        time.sleep(1)

    return all_articles


if __name__ == "__main__":
    # 示例配置
    BIZ = "MzYzOTU1NTUzNw=="
    ALBUM_ID = "4319761724883959819"

    # 认证参数（通过 mitmproxy 抓包获取）
    AUTH = {
        "appmsg_token": "your_token_here",
        "uin": "your_uin_here",
        "key": "your_key_here",
        "pass_ticket": "your_pass_ticket_here"
    }

    articles = fetch_album_articles(BIZ, ALBUM_ID, AUTH)
    print(f"共获取 {len(articles)} 篇文章")
