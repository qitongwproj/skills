"""
批量获取微信公众号专辑文章链接
"""
import urllib.request
import json
import os
import time

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "articles")
AUTH_FILE = os.path.join(OUTPUT_DIR, "auth.json")


def _load_auth():
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _print_auth_guide():
    print("""
╔══════════════════════════════════════════════════════════════╗
║  该专辑翻页需要认证参数，请通过 mitmproxy 抓取：            ║
║                                                            ║
║  1. 安装 mitmproxy:                                        ║
║     pip install mitmproxy                                  ║
║                                                            ║
║  2. 启动抓包:                                              ║
║     mitmdump -s scripts/mitm_capture.py -p 8080            ║
║                                                            ║
║  3. 手机配置代理为 <本机IP>:8080，安装 mitmproxy 证书       ║
║                                                            ║
║  4. 在微信中打开该专辑页面，终端会打印认证参数               ║
║                                                            ║
║  5. 将参数写入 articles/auth.json:                          ║
║     {                                                      ║
║       "appmsg_token": "...",                               ║
║       "uin": "...",                                        ║
║       "key": "...",                                        ║
║       "pass_ticket": "..."                                 ║
║     }                                                      ║
║                                                            ║
║  6. 重新运行本脚本即可自动加载认证参数                       ║
╚══════════════════════════════════════════════════════════════╝
""")


def fetch_album_articles(biz, album_id, auth_params=None):
    """
    获取专辑全部文章链接。
    优先使用传入的 auth_params，其次尝试从 articles/auth.json 加载。

    Args:
        biz: 公众号唯一标识
        album_id: 专辑ID
        auth_params: 认证参数字典，为 None 时自动尝试加载 auth.json

    Returns:
        list: 文章列表，每项包含 title, url, mid
    """
    if auth_params is None:
        auth_params = _load_auth()

    all_articles = []
    seen_mids = set()
    begin_msgid = ""
    page = 0
    auth_needed = False

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                      "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
                      "MicroMessenger/8.0.38"
    }

    while True:
        page += 1

        if begin_msgid:
            if auth_params:
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
                url = (
                    f"https://mp.weixin.qq.com/mp/appmsgalbum?__biz={biz}"
                    f"&action=getalbum&album_id={album_id}"
                    f"&begin_msgid={begin_msgid}&begin_itemidx=1&count=10&f=json"
                )
        else:
            url = f"https://mp.weixin.qq.com/mp/appmsgalbum?__biz={biz}&action=getalbum&album_id={album_id}&f=json"

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        articles = data.get("getalbum_resp", {}).get("article_list", [])
        continue_flag = data.get("getalbum_resp", {}).get("continue_flag", "0")

        new_count = 0
        for article in articles:
            mid = article["msgid"]
            if mid not in seen_mids:
                seen_mids.add(mid)
                all_articles.append({
                    "title": article["title"].split("\n")[0],
                    "url": article["url"].replace("http://", "https://"),
                    "mid": mid
                })
                new_count += 1
            begin_msgid = mid

        print(f"  第{page}页: {len(articles)}篇(新增{new_count}), continue={continue_flag}, 累计={len(all_articles)}")

        if continue_flag != "1":
            break

        if new_count == 0 and not auth_params:
            auth_needed = True
            break

        time.sleep(1)

    if auth_needed:
        print("\n⚠️  翻页失败：无认证参数时返回了重复文章，该专辑需要认证。")
        _print_auth_guide()

    return all_articles


if __name__ == "__main__":
    BIZ = "MzYzOTU1NTUzNw=="
    ALBUM_ID = "4319761724883959819"

    articles = fetch_album_articles(BIZ, ALBUM_ID)
    print(f"\n共获取 {len(articles)} 篇文章")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "articles.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"已保存到: {output_path}")