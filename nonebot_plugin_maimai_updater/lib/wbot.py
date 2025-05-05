from datetime import datetime
from typing import Optional

import httpx
from nonebot import logger
from nonebot_plugin_saa import Image, Text
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from .db import Token
from .utils import send_to_super
from .wahlap import Wahlap
from .wechat import WeChat

_wahlap: Optional[Wahlap] = None


def get_wahlap() -> Wahlap:
    if _wahlap is None:
        raise ValueError("maimaiBot has not been initialized.")
    return _wahlap


async def save_token(sess: AsyncSession, token: str, userid: str):
    obj = await sess.get(Token, 0)
    if obj:
        obj.token = token
        obj.userid = userid
    else:
        obj = Token(id=0, token=token, userid=userid)
        sess.add(obj)
    await sess.commit()


async def init_wahlap(sess: AsyncSession):
    global _wahlap
    if not _wahlap:
        try:
            maitoken = await sess.get(Token, 0)
            if maitoken:
                _wahlap = Wahlap(
                    maitoken.token, maitoken.userid, lambda t, i: save_token(sess, t, i)
                )
            else:
                _wahlap = Wahlap(None, None, lambda t, i: save_token(sess, t, i))
        except Exception as e:
            logger.exception(e)
            await send_to_super("maibot: create bot client err: " + str(e))


async def check_token(
    sess: AsyncSession, force: bool = False, terminal: bool = False
) -> bool:
    global _wahlap
    expired = not _wahlap or await _wahlap.is_token_expired()
    isactived = not (
        4 <= datetime.now(tz=ZoneInfo("Asia/Shanghai")).hour
        and datetime.now(tz=ZoneInfo("Asia/Shanghai")).hour <= 6
    )
    if (expired and isactived) or force:
        try:
            wc = WeChat()
            uuid = await wc.get_login_uuid()

            async with httpx.AsyncClient() as client:
                resp = await client.get("https://login.weixin.qq.com/qrcode/" + uuid)
                await send_to_super(Image(resp.content) + Text("maibot: token expired"))
                if terminal:
                    with open("qrcode.png", "wb") as qr:
                        qr.write(resp.content)
                await resp.aclose()

            await wc.wait_login()
            await send_to_super("maibot: wechat login success")
            if terminal:
                logger.info("maibot: wechat login success")
            maitoken = await wc.get_maitoken()

            if _wahlap:
                _wahlap.set_token(*maitoken)
            else:
                _wahlap = Wahlap()

            await save_token(sess, maitoken[0], maitoken[1])

            await send_to_super("maibot: refresh token success")
            if terminal:
                logger.info("maibot: refresh token success")
            return True
        except Exception as e:
            logger.exception(e)
            await send_to_super(
                "maibot: refresh token failed: "
                + str(type(e)).split(".")[-1]
                + ": "
                + str(e)
            )
            if terminal:
                logger.info(
                    "maibot: refresh token failed: "
                    + str(type(e)).split(".")[-1]
                    + ": "
                    + str(e)
                )
    return False
