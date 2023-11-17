from typing import Any, Callable, Iterable, NoReturn, Optional, Union

from nonebot import get_bots, get_driver
from nonebot.dependencies import Dependent
from nonebot.exception import FinishedException, RejectedException
from nonebot.internal.adapter import Event
from nonebot.internal.params import Depends
from nonebot.matcher import Matcher
from nonebot.typing import T_Handler
from nonebot_plugin_saa import (
    MessageFactory,
    TargetQQGuildChannel,
    TargetQQGuildDirect,
    TargetQQGroup,
    TargetQQPrivate,
    Text,
)

from .. import plugin_config


async def send_to_super(msg: MessageFactory | str):
    for bot in get_bots().values():
        for suser in get_driver().config.superusers:
            if isinstance(msg, str):
                msg = Text(msg)
            await msg.send_to(TargetQQPrivate(user_id=suser), bot)
        if plugin_config.super_group:
            if isinstance(msg, str):
                msg = Text(msg)
            await msg.send_to(TargetQQGroup(group_id=plugin_config.super_group), bot)
        if plugin_config.super_channel:
            if isinstance(msg, str):
                msg = Text(msg)
            await msg.send_to(TargetQQGuildChannel(channel_id=plugin_config.super_channel), bot)
        if plugin_config.super_guild_users:
            for suser in plugin_config.super_guild_users:
                split = suser.split("/")
                if isinstance(msg, str):
                    msg = Text(msg)
                await msg.send_to(TargetQQGuildDirect(recipient_id=split[1], source_guild_id=split[0]), bot)



async def send_with_reply(msg: MessageFactory | str):
    """带reply回复消息，仅能用在事件响应器中"""
    if isinstance(msg, str):
        msg = Text(msg)
    await msg.send(reply=True)


def add_parameterless(matcher: Matcher, parameterless: Optional[Iterable[Any]] = None):
    def _decorator(func: T_Handler) -> T_Handler:
        func_handler = matcher.handlers[-1]
        new_handler = Dependent(
            call=func_handler.call,
            params=func_handler.params,
            parameterless=Dependent.parse_parameterless(
                tuple(parameterless), matcher.HANDLER_PARAM_TYPES
            )
            + func_handler.parameterless,
        )
        matcher.handlers[-1] = new_handler

        return func

    return _decorator


def got_with_reply(
    matcher: Matcher,
    key: str,
    prompt: Optional[Union[MessageFactory, str]] = None,
    parameterless: Optional[Iterable[Any]] = None,
) -> Callable[[T_Handler], T_Handler]:
    """装饰一个函数来指示 NoneBot 获取一个参数 `key`

    当要获取的 `key` 不存在时接收用户新的一条消息再运行该函数，
    如果 `key` 已存在则直接继续运行

    参数:
        key: 参数名
        prompt: 在参数不存在时向用户发送的消息 (自动添加回复)
        parameterless: 非参数类型依赖列表
    """

    async def _key_getter(event: Event, matcher: "Matcher"):
        matcher.set_target(key)
        if matcher.get_target() == key:
            matcher.set_arg(key, event.get_message())
            return
        if matcher.get_arg(key, ...) is not ...:
            return
        await send_with_reply(prompt)
        await matcher.reject()

    _parameterless = (Depends(_key_getter), *(parameterless or ()))

    def _decorator(func: T_Handler) -> T_Handler:
        if matcher.handlers and matcher.handlers[-1].call is func:
            func_handler = matcher.handlers[-1]
            new_handler = Dependent(
                call=func_handler.call,
                params=func_handler.params,
                parameterless=Dependent.parse_parameterless(
                    tuple(_parameterless), matcher.HANDLER_PARAM_TYPES
                )
                + func_handler.parameterless,
            )
            matcher.handlers[-1] = new_handler
        else:
            matcher.append_handler(func, parameterless=_parameterless)

        return func

    return _decorator


async def reject_with_reply(
    prompt: Optional[Union[MessageFactory, str]] = None,
) -> NoReturn:
    """最近使用 `got` / `receive` 接收的消息不符合预期，
    发送一条消息给当前交互用户并将当前事件处理流程中断在当前位置，在接收用户新的一个事件后从头开始执行当前处理函数

    参数:
        prompt: 消息内容 (自动添加回复)
    """
    if prompt is not None:
        await send_with_reply(prompt)
    raise RejectedException


async def finish_with_reply(
    message: Optional[Union[MessageFactory, str]] = None,
) -> NoReturn:
    """回复一条消息给当前交互用户并结束当前事件响应器

    参数:
        message: 消息内容 (自动添加回复)
    """
    if message is not None:
        await send_with_reply(message)
    raise FinishedException
