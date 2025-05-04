import re
from typing import Awaitable, Callable, Optional

import httpx

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; U; UOS x86_64; zh-cn) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 UOSBrowser/6.0.1.1001",  # noqa: E501
}


class BaseError(Exception):
    ...


class NoTokenError(BaseError):
    def __str__(self) -> str:
        return "no token"


class ValidateBodyError(BaseError):
    ...


class ApiError(BaseError):
    ...


class Wahlap:
    client: httpx.AsyncClient
    on_token_change: Callable[[str, str], Awaitable[None]]

    def __init__(
        self,
        token: Optional[str],
        userid: Optional[str],
        on_token_change: Callable[[str, str], Awaitable[None]],
    ) -> None:
        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=300,  # TODO: check if dev
        )

        if token and userid:
            self.set_token(token, userid)

        self.on_token_change = on_token_change

    def set_token(self, token: str, userid: str):
        self.client.cookies.set("_t", token, "maimai.wahlap.com")
        self.client.cookies.set("userId", userid, "maimai.wahlap.com")

    async def requset(self, req: httpx.Request) -> httpx.Response:
        old_token = self.client.cookies.get("_t", domain="maimai.wahlap.com")
        old_userid = self.client.cookies.get("userId", domain="maimai.wahlap.com")
        if old_token is None or old_userid is None:
            raise NoTokenError()

        resp = await self.client.send(req, follow_redirects=(req.method == "GET"))

        new_token = self.client.cookies.get("_t", domain="maimai.wahlap.com")
        new_userid = self.client.cookies.get("userId", domain="maimai.wahlap.com")
        if old_token != new_token or old_userid != new_userid:
            await self.on_token_change(new_token, new_userid)

        return resp

    @staticmethod
    def validate_body(body: str, msg: str):
        if "错误码：" in body:
            result = re.search(r"错误码：(\d*)", body)
            raise ValidateBodyError(msg + result[1])

    async def is_token_expired(self) -> bool:
        req = self.client.build_request(
            "HEAD", "https://maimai.wahlap.com/maimai-mobile/home/"
        )
        try:
            resp = await self.requset(req)
            return resp.status_code != 200
        except NoTokenError:
            return True

    async def validate_friend_code(self, idx: str) -> bool:
        req = self.client.build_request(
            "GET",
            "https://maimai.wahlap.com/maimai-mobile/friend/search/searchUser/?friendCode="
            + idx,
        )

        resp = await self.requset(req)
        self.validate_body(resp.text, "validate friend code failed: ")

        if "找不到该玩家" in resp.text:
            return False

        return True

    async def _send_friend_api(self, uri: str, **kwargs: str) -> httpx.Response:
        token = self.client.cookies.get("_t", domain="maimai.wahlap.com")
        if token is None:
            raise NoTokenError()

        req = self.client.build_request(
            "POST",
            "https://maimai.wahlap.com" + uri,
            data=({"token": token} | kwargs),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        resp = await self.requset(req)
        if (code := resp.status_code) != 200 and code != 302:
            raise ApiError("api request failed: " + code)

        return resp

    async def send_friend_requset(self, idx: str):
        await self._send_friend_api(
            "/maimai-mobile/friend/search/invite/", idx=idx, invite=""
        )

    async def cancel_friend_requset(self, idx: str):
        await self._send_friend_api(
            "/maimai-mobile/friend/invite/cancel/", idx=idx, invite=""
        )

    async def get_sent_friend_requsets(self) -> list[str]:
        req = self.client.build_request(
            "GET", "https://maimai.wahlap.com/maimai-mobile/friend/invite/"
        )

        resp = await self.requset(req)
        self.validate_body(resp.text, "get sent request list failed: ")

        return re.findall(r'<input type="hidden" name="idx" value="(.*?)"', resp.text)

    async def allow_friend_requset(self, idx: str):
        pass  # TODO

    async def block_friend_requset(self, idx: str):
        pass  # TODO

    async def remove_friend(self, idx: str):
        pass  # TODO

    async def get_friend_list(self) -> list[str]:
        req = self.client.build_request(
            "GET", "https://maimai.wahlap.com/maimai-mobile/friend/"
        )

        resp = await self.requset(req)
        self.validate_body(resp.text, "get friend list failed: ")

        return re.findall(r'<input type="hidden" name="idx" value="(.*?)"', resp.text)

    async def favorite_on_friend(self, idx: str):
        await self._send_friend_api("/maimai-mobile/friend/favoriteOn/", idx=idx)

    async def favorite_off_friend(self, idx: str):
        await self._send_friend_api("/maimai-mobile/friend/favoriteOff/", idx=idx)

    async def get_friend_vs(
        self,
        idx: str,
        score_type: int,
        diff: int,
        only_played: Optional[bool] = False,
        only_lose: Optional[bool] = False,
        only_win: Optional[bool] = False,
    ) -> str:
        params = {"genre": "99", "scoreType": score_type, "diff": diff, "idx": idx}
        if only_played:
            params = params | {"playCheck": "on"}
        if only_lose:
            params = params | {"loseOnly": "on"}
        if only_win:
            params = params | {"winOnly": "on"}

        req = self.client.build_request(
            "GET",
            "https://maimai.wahlap.com/maimai-mobile/friend/friendGenreVs/battleStart/",
            params=params,
        )

        resp = await self.requset(req)
        self.validate_body(resp.text, "get friend vs failed: ")

        return resp.text
