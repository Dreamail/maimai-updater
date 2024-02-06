import asyncio

import httpx
from arclet.alconna import Alconna, Subcommand
from nonebot import on_command
from nonebot.adapters import Event
from nonebot.exception import FinishedException
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, Depends
from nonebot.rule import to_me
from nonebot_plugin_alconna import on_alconna

from . import utils
from .db import User, get_or_create_user, update_user
from .prober import DIFF, update_score
from .wbot import check_token, get_wahlap

mai = on_command("maip", force_whitespace=True, block=True, rule=to_me())
bind = on_command("maib", force_whitespace=True, block=True, rule=to_me())
update = on_command("maiu", force_whitespace=True, block=True, rule=to_me())

debug = on_alconna(
    Alconna(["/"], "debug", Subcommand("retoken")), block=True, rule=to_me()
)


@mai.handle()
async def _():
    await utils.finish_with_reply(
        """
        指令列表：
        /maib 交互式绑定账号
        /maiu 更新成绩

        注：maip是指maimai prober
        """.strip().replace("    ", "")
    )


async def pre_bind(matcher: Matcher, event: Event):
    user = await get_or_create_user(event.get_user_id())
    if user.maimai_id and user.token and not matcher.state.get("rebind", False):
        if matcher.get_target() == "confirm":
            if event.get_plaintext() == "是":
                matcher.state["rebind"] = True
                return
            elif event.get_plaintext() == "否":
                await utils.finish_with_reply("绑定取消")
            else:
                matcher.set_target("confirm")
                await utils.reject_with_reply("回复「是」重新绑定，回复「否」取消绑定")

        else:
            matcher.set_target("confirm")
            await utils.send_with_reply("你已经绑定过啦！")
            await utils.reject_with_reply("回复「是」重新绑定，回复「否」取消绑定")

    matcher.state["muser"] = user
    return


@utils.add_parameterless(bind, [Depends(pre_bind)])
@utils.got_with_reply(bind, "token", "请「回复」我你的查分器更新token～")
@utils.got_with_reply(bind, "mid", "请「回复」我你的maimai好友代码～")
async def _(matcher: Matcher, token: str = ArgPlainText(), mid: str = ArgPlainText()):
    token = token.strip()
    mid = mid.strip()
    user: User = matcher.state["muser"]
    wl = get_wahlap()

    # bind prober
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.diving-fish.com/api/maimaidxprober/token_available",
                params={"token": token},
            )
            if resp.status_code == 404:
                await utils.finish_with_reply("查分器账号token有误，请检查一下哦")
            if resp.status_code != 200:
                await utils.send_to_super(
                    "on bind: (" + resp.status_code + ")" + await resp.text
                )
                await utils.finish_with_reply(
                    "登录查分器出错啦，请稍后再试或联系管理员"
                )
    except FinishedException:
        raise
    except Exception as e:
        await utils.send_to_super("on bind: " + str(e))
        await utils.finish_with_reply("登录查分器出错啦，请稍后再试或联系管理员")

    user.token = token

    # bind maimai
    try:
        if not await wl.validate_friend_code(mid):
            await utils.finish_with_reply("找不到你哟，请检查好友ID是否正确")
    except RuntimeError as e:
        await utils.send_to_super("on bind: " + str(e))
        await utils.finish_with_reply("找你找出错啦，请稍后再试或联系管理员")

    try:
        friend_list = await wl.get_friend_list()
        if mid in friend_list:
            user.maimai_id = mid
            await update_user(user)
            await utils.finish_with_reply("你已经是好友了，所以绑定成功啦！")

        sent_list = await wl.get_sent_friend_requsets()
        if mid in sent_list:
            user.maimai_id = mid
            await update_user(user)
            await utils.finish_with_reply(
                "已经给你发过好友请求了啦，同意好友申请就完成绑定啦！"
            )
    except RuntimeError as e:
        await utils.send_to_super("on bind: " + str(e))
        await utils.finish_with_reply("添加好友失败了，请稍后再试或联系管理员")

    try:
        await wl.send_friend_requset(mid)
    except RuntimeError as e:
        await utils.send_to_super("on bind: " + str(e))
        await utils.finish_with_reply("发送好友请求失败，请稍后再试或联系管理员")

    user.maimai_id = mid
    await update_user(user)
    await utils.finish_with_reply("给你发送好友请求啦，同意好友申请就完成绑定啦！")


@update.handle()
async def _(event: Event):
    user: User = await get_or_create_user(event.get_user_id())
    wl = get_wahlap()

    if not user.maimai_id:
        await utils.finish_with_reply("你还未绑定maimai账户，先进行一个账户绑定吧！")
    if not user.token:
        await utils.finish_with_reply("你还未绑定查分器账户，先进行一个账户绑定吧！")

    await utils.send_with_reply("开始更新成绩～")

    try:
        await wl.favorite_on_friend(user.maimai_id)
    except RuntimeError as e:
        await utils.send_to_super("on update: " + str(e))
        await utils.finish_with_reply("把你登陆到喜爱失败惹，请稍后再试或联系管理员")

    async def _wap(coro):
        try:
            result = await coro
        except Exception as e:
            result = e
            await utils.send_to_super("on update: " + str(e))
        return result

    results = await asyncio.gather(
        _wap(update_score(wl, user.token, user.maimai_id, 0)),
        _wap(update_score(wl, user.token, user.maimai_id, 1)),
        _wap(update_score(wl, user.token, user.maimai_id, 2)),
        _wap(update_score(wl, user.token, user.maimai_id, 3)),
        _wap(update_score(wl, user.token, user.maimai_id, 4)),  # quite stupid
    )

    err_diffs = []
    for diff, result in enumerate(results):
        if isinstance(result, Exception):
            err_diffs.append(DIFF[diff])
    if len(err_diffs) != 0:
        await utils.send_with_reply(
            "更新{diff}难度时出现问题，请稍后再试或联系管理员".format(
                diff=", ".join(err_diffs)
            )  # noqa: E501
        )
    else:
        await utils.send_with_reply("所有成绩更新完成！")

    try:
        await wl.favorite_off_friend(user.maimai_id)
    except RuntimeError as e:
        utils.send_to_super("on update: " + str(e))


@debug.assign("retoken")
async def _():
    success = await check_token(force=True)
    await utils.send_with_reply("token刷新成功！" if success else "token刷新失败")
