import urllib.request

WECHAT_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
    "MicroMessenger/8.0.38"
)


def fetch_html(url):
    url = url.replace("#rd", "").replace("http://", "https://")
    req = urllib.request.Request(url, headers={"User-Agent": WECHAT_UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")