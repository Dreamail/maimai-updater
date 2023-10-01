from datetime import datetime
from typing import Optional

from nonebot import logger
from nonebot_plugin_saa import Image, Text
from zoneinfo import ZoneInfo

from .db import get_token, save_token
from .utils import send_to_super
from .wahlap import Wahlap
from .wechat import WeChat

_wahlap: Optional[Wahlap] = None


def get_wahlap() -> Wahlap:
    if _wahlap is None:
        raise ValueError("maimaiBot has not been initialized.")
    return _wahlap


async def init_wahlap():
    global _wahlap
    if not _wahlap:
        try:
            maitoken = await get_token()
            if maitoken:
                _wahlap = Wahlap(*maitoken, save_token)
            else:
                _wahlap = Wahlap(None, None, save_token)
        except Exception as e:
            logger.exception(e)
            await send_to_super("maibot: create bot client err: " + str(e))


async def check_token():
    global _wahlap
    if (not _wahlap or await _wahlap.is_token_expired()) and not (
        4 <= datetime.now(tz=ZoneInfo("Asia/Shanghai")).hour
        and datetime.now(tz=ZoneInfo("Asia/Shanghai")).hour <= 6
    ):
        try:
            wc = WeChat()
            uuid = await wc.get_login_uuid()

            await send_to_super(
                Image("https://login.weixin.qq.com/qrcode/" + uuid)
                + Text("maibot: token expired")
            )

            await wc.wait_login()
            await send_to_super("maibot: wechat login success")
            maitoken = await wc.get_maitoken()

            if _wahlap:
                _wahlap.set_token(*maitoken)
            else:
                _wahlap = Wahlap()
            await save_token(*maitoken)

            await send_to_super("maibot: refresh token success")
        except Exception as e:
            logger.exception(e)
            await send_to_super(
                "maibot: refresh token failed: " + str(type(e)) + ": " + str(e)
            )
