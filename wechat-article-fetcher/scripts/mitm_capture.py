"""
mitmproxy 抓包脚本，用于捕获微信认证参数
"""


def request(flow):
    """捕获请求中的认证参数"""
    url = flow.request.url

    if "mp.weixin.qq.com/mp/appmsgalbum" in url:
        # 提取关键参数
        params = ["appmsg_token", "key", "uin", "pass_ticket"]
        captured = {}

        for param in params:
            value = flow.request.query.get(param, "")
            if value:
                captured[param] = value

        if captured:
            print("\n" + "="*50)
            print("捕获到认证参数:")
            for k, v in captured.items():
                print(f"  {k}: {v}")
            print("="*50 + "\n")
