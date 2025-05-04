from nonebot import on_command
from nonebot.adapters import Event

from nonebot_plugin_orm import async_scoped_session

from . import utils
from .db import User, get_all_update_times

update = on_command(
    "maiu", force_whitespace=True, block=False, priority=0, rule=utils.not_me
)
stat = on_command("mais", force_whitespace=True, block=True, rule=utils.not_me)


@update.handle()
async def _(event: Event, sess: async_scoped_session):
    user = await User.from_id(event.get_user_id(), sess)
    if not user:
        return
    if not user.update_times:
        user.update_times = 1
    else:
        user.update_times += 1
    await sess.commit()


@stat.handle()
async def _(sess: async_scoped_session):
    await utils.finish_with_reply(
        "自统计上线以来，幽凛酱已经完成了"
        + str(await get_all_update_times(sess))
        + "次成绩更新啦！"
    )
