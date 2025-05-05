import re
import time
from urllib.parse import urlparse, parse_qs

import httpx

jslogin = "https://login.wx.qq.com/jslogin"
webwxnewloginpage = (
    "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?mod=desktop"
)
webwxlogout = "/cgi-bin/mmwebwx-bin/webwxlogout"
login = "https://login.wx.qq.com/cgi-bin/mmwebwx-bin/login"
appid = "wx782c26e4c19acffb"
uos_ver = "2.0.0"
uos_ext = "Go8FCIkFEokFCggwMDAwMDAwMRAGGvAESySibk50w5Wb3uTl2c2h64jVVrV7gNs06GFlWplHQbY/5FfiO++1yH4ykCyNPWKXmco+wfQzK5R98D3so7rJ5LmGFvBLjGceleySrc3SOf2Pc1gVehzJgODeS0lDL3/I/0S2SSE98YgKleq6Uqx6ndTy9yaL9qFxJL7eiA/R3SEfTaW1SBoSITIu+EEkXff+Pv8NHOk7N57rcGk1w0ZzRrQDkXTOXFN2iHYIzAAZPIOY45Lsh+A4slpgnDiaOvRtlQYCt97nmPLuTipOJ8Qc5pM7ZsOsAPPrCQL7nK0I7aPrFDF0q4ziUUKettzW8MrAaiVfmbD1/VkmLNVqqZVvBCtRblXb5FHmtS8FxnqCzYP4WFvz3T0TcrOqwLX1M/DQvcHaGGw0B0y4bZMs7lVScGBFxMj3vbFi2SRKbKhaitxHfYHAOAa0X7/MSS0RNAjdwoyGHeOepXOKY+h3iHeqCvgOH6LOifdHf/1aaZNwSkGotYnYScW8Yx63LnSwba7+hESrtPa/huRmB9KWvMCKbDThL/nne14hnL277EDCSocPu3rOSYjuB9gKSOdVmWsj9Dxb/iZIe+S6AiG29Esm+/eUacSba0k8wn5HhHg9d4tIcixrxveflc8vi2/wNQGVFNsGO6tB5WF0xf/plngOvQ1/ivGV/C1Qpdhzznh0ExAVJ6dwzNg7qIEBaw+BzTJTUuRcPk92Sn6QDn2Pu3mpONaEumacjW4w6ipPnPw+g2TfywJjeEcpSZaP4Q3YV5HG8D6UjWA4GSkBKculWpdCMadx0usMomsSS/74QgpYqcPkmamB4nVv1JxczYITIqItIKjD35IGKAUwAA=="  # noqa: E501
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; U; UOS x86_64; zh-cn) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 UOSBrowser/6.0.1.1001",  # noqa: E501
    "client-version": uos_ver,
    "extspam": uos_ext,
}
maimai_auth = "https://tgk-wcaime.wahlap.com/wc_auth/oauth/authorize/maimai-dx"
maimai_req = "/cgi-bin/mmwebwx-bin/webwxcheckurl"


class WeChat:
    client: httpx.AsyncClient = httpx.AsyncClient(headers=headers, timeout=300)
    uuid: str
    domain: str

    async def get_login_uuid(self) -> str:
        params = {
            "redirect_uri": webwxnewloginpage,
            "appid": appid,
            "fun": "new",
            "lang": "zh_CN",
            "_": int(time.time()),
        }

        resp = await self.client.get(jslogin, params=params)
        result = re.search(r'uuid = "(.*?)";', resp.text)
        await resp.aclose()
        if result is None:
            raise Exception("cant fetch uuid")
        self.uuid = result[1]
        return result[1]

    async def wait_login(self):
        now = int(time.time())
        params = {
            "r": int(now / 1579),
            "_": now,
            "loginicon": "true",
            "uuid": self.uuid,
            "tip": 1,
        }

        redirect_uri = ""
        while True:
            resp = await self.client.get(login, params=params, timeout=30)
            result = re.search(r"window.code=(\d+);", resp.text)
            await resp.aclose()
            if result is None:
                continue

            match result[1]:
                case "200":
                    result = re.search(r'window.redirect_uri="(.*?)"', resp.text)
                    if result is None:
                        raise Exception("cant fetch redirect uri")
                    redirect_uri = result[1]
                    break
                case "400":
                    raise Exception("login time out")

            if params["tip"] == 1:
                params["tip"] = 0

        redirect_params = parse_qs(urlparse(redirect_uri).query)
        params.update(redirect_params)
        resp = await self.client.get(redirect_uri, params=params)
        self.domain = resp.url.host
        await resp.aclose()

    async def get_maitoken(self) -> tuple[str, str]:
        resp = await self.client.get(maimai_auth)
        params = {"requrl": resp.headers["Location"]}
        resp = await self.client.get(
            "https://" + self.domain + maimai_req, params=params, follow_redirects=True
        )

        return self.client.cookies.get("_t"), self.client.cookies.get("userId")
