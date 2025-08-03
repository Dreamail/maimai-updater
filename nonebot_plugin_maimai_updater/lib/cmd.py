import asyncio

import httpx
from arclet.alconna import Alconna, Subcommand, Args
from nonebot import on_command
from nonebot.adapters import Event
from nonebot.exception import FinishedException
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, Depends
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot_plugin_alconna import on_alconna, Match
from nonebot_plugin_alconna.params import Check, assign, merge_path
from nonebot_plugin_orm import async_scoped_session

from .. import plugin_config
from . import utils
from .db import USER, User
from .prober import DIFF, update_score, UploadError
from .wbot import check_token, get_wahlap
from .lxns import Lxns

mai = on_command(
    "maip", force_whitespace=True, priority=100, block=True, rule=utils.not_me
)
bind = on_alconna(
    Alconna(
        ["/"],
        "maib",
        Subcommand("df", Args["friend_code;?", str]["token;?", str]),
        Subcommand("lxns", Args["friend_code;?", str]),
        Subcommand("old"),
    ),
    priority=100,
    block=True,
    rule=to_me(),
)
update = on_command(
    "maiu", force_whitespace=True, priority=100, block=True, rule=utils.not_me
)

debug = on_alconna(
    Alconna(
        ["/"],
        "debug",
        Subcommand("retoken"),
        Subcommand("wahlap", Args["method", str]["url", str]),
    ),
    block=True,
    rule=to_me(),
    permission=SUPERUSER,
)


@mai.handle()
async def _():
    await utils.finish_with_reply(
        """
        指令列表：
        /maib df (friend_code) (token) 绑定水鱼查分器账号
        /maib lxns (friend_code) 绑定落雪查分器账号
        /maib old 交互式绑定账号（不再维护，仅水鱼查分器）
        /maiu 更新成绩
        /trans [图片] （反向）转生！ (仅蓝标Bot可用)

        注：maip是指maimai prober
        """.strip().replace("    ", "")
    )


async def pre_bind(matcher: Matcher, event: Event, user: USER, sess: async_scoped_session):
    if user and not matcher.state.get("rebind", False):
        if matcher.get_target() == "confirm":
            if event.get_plaintext().strip() == "是":
                matcher.state["rebind"] = True
                await sess.delete(user)
                return
            elif event.get_plaintext().strip() == "否":
                await utils.finish_with_reply("绑定取消")
            else:
                matcher.set_target("confirm")
                await utils.reject_with_reply("回复「是」重新绑定，回复「否」取消绑定")

        else:
            matcher.set_target("confirm")
            await utils.send_with_reply("你已经绑定过啦！")
            await utils.reject_with_reply("回复「是」重新绑定，回复「否」取消绑定")


@bind.assign("df", parameterless=[Depends(pre_bind)])
async def _(
    event: Event,
    sess: async_scoped_session,
    friend_code: Match[str],
    token: Match[str],
):
    if not friend_code.available or not token.available:
        await utils.finish_with_reply(
            """
            指令格式错误哦，请使用：
            /maib df (friend_code) (token) 绑定水鱼查分器账号
            """.strip().replace("    ", "")
        )

    friend_code = friend_code.result
    token = token.result

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

    # bind maimai
    wl = get_wahlap()
    try:
        if await wl.search_friend(friend_code) is None:
            await utils.finish_with_reply("找不到你哟，请检查好友ID是否正确")
    except RuntimeError as e:
        await utils.send_to_super("on bind: " + str(e))
        await utils.finish_with_reply("找你找出错啦，请稍后再试或联系管理员")

    try:
        friend_list = await wl.get_friend_list()
        if friend_code in friend_list:
            sess.add(
                User(user_id=event.get_user_id(), friend_id=friend_code, df_token=token)
            )
            await sess.commit()
            await utils.finish_with_reply("你已经是好友了，所以绑定成功啦！")

        sent_list = await wl.get_sent_friend_requsets()
        if friend_code in sent_list:
            sess.add(
                User(user_id=event.get_user_id(), friend_id=friend_code, df_token=token)
            )
            await sess.commit()
            await utils.finish_with_reply(
                "已经给你发过好友请求了啦，同意好友申请就完成绑定啦！"
            )
    except RuntimeError as e:
        await utils.send_to_super("on bind: " + str(e))
        await utils.finish_with_reply("添加好友失败了，请稍后再试或联系管理员")

    try:
        await wl.send_friend_requset(friend_code)
    except RuntimeError as e:
        await utils.send_to_super("on bind: " + str(e))
        await utils.finish_with_reply("发送好友请求失败，请稍后再试或联系管理员")

    sess.add(User(user_id=event.get_user_id(), friend_id=friend_code, df_token=token))
    await sess.commit()
    await utils.finish_with_reply("给你发送好友请求啦，同意好友申请就完成绑定啦！")


@bind.assign("lxns", parameterless=[Depends(pre_bind)])
async def _(
    event: Event,
    sess: async_scoped_session,
    friend_code: Match[str],
):
    if not friend_code.available:
        await utils.finish_with_reply(
            """
            指令格式错误哦，请使用：
            /maib lxns (friend_code) 绑定落雪查分器账号
            """.strip().replace("    ", "")
        )

    friend_code = friend_code.result

    create_new_player = False

    # bind prober
    lx = Lxns(token=plugin_config.lxns_token)
    try:
        resp = await lx.get_player(friend_code)
        if resp["code"] == 404:
            resp = await bind.prompt(
                """
                该玩家尚未创建落雪查分器账号，请回复「是」或「否」自动创建临时账号？
                三十秒超时后自动取消绑定。
                """.strip().replace("    ", ""),
                timeout=30,
            )
            if resp is None:
                await bind.finish("超时，绑定取消")
            create_new_player = resp.extract_plain_text().strip() == "是"
        elif resp["code"] == 403:
            await utils.finish_with_reply(
                "你的落雪查分器账号关闭了第三方查询权限，请到查分器设置中开启"
            )
        elif resp["code"] != 200:
            await utils.send_to_super(
                "on bind: (" + resp["code"] + ")" + await resp.text
            )
            await utils.finish_with_reply("登录查分器出错啦，请稍后再试或联系管理员")
    except FinishedException:
        raise
    except Exception as e:
        await utils.send_to_super("on bind: " + str(e))
        await utils.finish_with_reply("登录查分器出错啦，请稍后再试或联系管理员")

    # bind maimai
    wl = get_wahlap()
    try:
        search_result = await wl.search_friend(friend_code)
        if search_result is None:
            await utils.finish_with_reply("找不到你哟，请检查好友ID是否正确")
    except RuntimeError as e:
        await utils.send_to_super("on bind: " + str(e))
        await utils.finish_with_reply("找你找出错啦，请稍后再试或联系管理员")

    if create_new_player:
        try:
            await lx.create_player(
                search_result["name"],
                search_result["rating"],
                int(friend_code),
            )
        except Exception as e:
            await utils.send_to_super("on bind: " + str(e))
            await utils.finish_with_reply(
                "自动创建落雪查分器账号失败，请稍后再试或联系管理员"
            )

    try:
        friend_list = await wl.get_friend_list()
        if friend_code in friend_list:
            sess.add(User(user_id=event.get_user_id(), friend_id=friend_code))
            await sess.commit()
            await utils.finish_with_reply("你已经是好友了，所以绑定成功啦！")

        sent_list = await wl.get_sent_friend_requsets()
        if friend_code in sent_list:
            sess.add(User(user_id=event.get_user_id(), friend_id=friend_code))
            await sess.commit()
            await utils.finish_with_reply(
                "已经给你发过好友请求了啦，同意好友申请就完成绑定啦！"
            )
    except RuntimeError as e:
        await utils.send_to_super("on bind: " + str(e))
        await utils.finish_with_reply("添加好友失败了，请稍后再试或联系管理员")

    try:
        await wl.send_friend_requset(friend_code)
    except RuntimeError as e:
        await utils.send_to_super("on bind: " + str(e))
        await utils.finish_with_reply("发送好友请求失败，请稍后再试或联系管理员")

    sess.add(User(user_id=event.get_user_id(), friend_id=friend_code))
    await sess.commit()
    await utils.finish_with_reply("给你发送好友请求啦，同意好友申请就完成绑定啦！")


@utils.add_parameterless(
    bind, [Depends(pre_bind), Check(assign(merge_path("old", bind.basepath)))]
)
@utils.got_with_reply(bind, "token", "请「回复」我你的查分器更新token～")
@utils.got_with_reply(bind, "mid", "请「回复」我你的maimai好友代码～")
async def _(
    event: Event,
    sess: async_scoped_session,
    token: str = ArgPlainText(),
    mid: str = ArgPlainText(),
):
    token = token.strip()
    mid = mid.strip()
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

    # bind maimai
    try:
        if not await wl.search_friend(mid):
            await utils.finish_with_reply("找不到你哟，请检查好友ID是否正确")
    except RuntimeError as e:
        await utils.send_to_super("on bind: " + str(e))
        await utils.finish_with_reply("找你找出错啦，请稍后再试或联系管理员")

    try:
        friend_list = await wl.get_friend_list()
        if mid in friend_list:
            sess.add(User(user_id=event.get_user_id(), friend_id=mid, df_token=token))
            await sess.commit()
            await utils.finish_with_reply("你已经是好友了，所以绑定成功啦！")

        sent_list = await wl.get_sent_friend_requsets()
        if mid in sent_list:
            sess.add(User(user_id=event.get_user_id(), friend_id=mid, df_token=token))
            await sess.commit()
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

    sess.add(User(user_id=event.get_user_id(), friend_id=mid, df_token=token))
    await sess.commit()
    await utils.finish_with_reply("给你发送好友请求啦，同意好友申请就完成绑定啦！")


@update.handle()
async def _(event: Event, user: USER):
    wl = get_wahlap()

    if not user:
        await utils.finish_with_reply(
            '你还未绑定账户，先进行一个账户绑定吧！\n也许你绑定过了，那就试试对蓝标Bot使用"/trans [图片]"指令8！'
        )

    await utils.send_with_reply("开始更新成绩～")

    try:
        await wl.favorite_on_friend(user.friend_id)
    except RuntimeError as e:
        await utils.send_to_super("on update: " + str(e))
        await utils.finish_with_reply("把你登陆到喜爱失败惹，请稍后再试或联系管理员")

    async def _wap(coro):
        try:
            result = await coro
        except Exception as e:
            result = e
            await utils.send_to_super(
                "on update: {type}: {errstr}".format(type=type(e), errstr=str(e))
            )
        return result

    tasks = [
        _wap(update_score(wl, user.df_token, user.friend_id, i, plugin_config.strict))
        for i in range(5)
    ]
    results = await asyncio.gather(*tasks)

    err_diffs = []
    df_err = False
    for diff, result in enumerate(results):
        if isinstance(result, Exception):
            err_diffs.append(DIFF[diff])
            if isinstance(result, UploadError):
                df_err = True

    if len(err_diffs) != 0:
        await utils.send_with_reply(
            "更新{diff}难度".format(diff=", ".join(err_diffs))
            + (
                "时出现问题，"
                if not df_err
                else "成绩时水鱼报错啦，成功与否是薛定谔的猫，更新失败"
            )
            + "请稍后再试或联系管理员"
        )
    else:
        await utils.send_with_reply("所有成绩更新完成！")

    try:
        await wl.favorite_off_friend(user.friend_id)
    except RuntimeError as e:
        utils.send_to_super("on update: " + str(e))


@debug.assign("retoken")
async def _(sess: async_scoped_session):
    success = await check_token(sess, force=True)
    await utils.send_with_reply("token刷新成功！" if success else "token刷新失败")


@debug.assign("wahlap")
async def _(method: str, url: str):
    wl = get_wahlap()
    req = wl.client.build_request(
        method=method.upper(),
        url=url,
    )
    resp = await wl.requset(req)
    if resp.status_code == 200:
        await utils.send_with_reply(
            "请求成功！\n" + resp.content.decode() if resp.content else "请求成功！"
        )
    else:
        await utils.send_with_reply(
            "请求失败，状态码：{code}\n{body}".format(
                code=resp.status_code, body=await resp.text()
            )
        )
