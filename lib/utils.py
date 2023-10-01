from typing import Any, Iterable, Optional

from nonebot import get_bots, get_driver
from nonebot.dependencies import Dependent
from nonebot.matcher import Matcher
from nonebot.typing import T_Handler
from nonebot_plugin_saa import MessageFactory, TargetQQPrivate, Text


async def send_to_super(msg: MessageFactory | str):
    for bot in get_bots().values():
        for suser in get_driver().config.superusers:
            if isinstance(msg, str):
                msg = Text(msg)
            await msg.send_to(TargetQQPrivate(user_id=suser), bot)


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
