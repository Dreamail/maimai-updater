import base64
import re

from nonebot import on_command
from nonebot.adapters.qq.event import QQMessageEvent
from nonebot.matcher import Matcher
from nonebot.rule import to_me
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select

from . import utils
from .db import User

trans = on_command("trans", block=True, rule=to_me() & utils.not_me)


@trans.handle()
async def _(matcher: Matcher, event: QQMessageEvent, sess: async_scoped_session):
    uin = ""
    if not event.attachments:
        await matcher.finish("你得带一张图片.heic")
    a = event.attachments[0]
    if a.content_type.find("image") != -1 and a.url:
        if a.url.find("gchat.qpic.cn") != -1:
            uin = re.findall(r"vuin=(\d+)&", a.url)[0]

        if a.url.find("multimedia.nt.qq.com.cn") != -1:
            pb = re.findall(r"fileid=(\S{16})", a.url)[0]
            uin = base64.b64decode(pb)[2:].decode()
    else:
        await matcher.finish("你得带一张图片.heic")

    if uin != "":
        user = (
            await sess.execute(select(User).where(User.user_id == event.get_user_id()))
        ).scalar_one_or_none()
        if user:
            user.sec_id = uin
            await sess.commit()
            await matcher.finish("跨端绑定成功！")

        user = (
            await sess.execute(select(User).where(User.user_id == uin))
        ).scalar_one_or_none()
        if user:
            user.sec_id = event.get_user_id()
            await sess.commit()
            await matcher.finish("跨端绑定成功！")

        await matcher.finish("跨端绑定失败喵")
