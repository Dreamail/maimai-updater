from nonebot import get_driver, get_plugin_config, logger, require

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler  # noqa: E402
from nonebot_plugin_orm import async_scoped_session  # noqa: E402

driver = get_driver()

from .config import Config  # noqa: E402

plugin_config = get_plugin_config(Config)

from .lib import wbot  # noqa: E402

_init = False


@driver.on_bot_connect
async def init(sess: async_scoped_session):
    global _init
    if _init:
        return
    _init = True
    logger.info("init maibot...")
    await wbot.init_wahlap(sess)
    logger.info("check maimai token...")
    await wbot.check_token(sess)
    logger.info("prober init successfully")

    scheduler.add_job(wbot.check_token, trigger="interval", args=[sess], hours=1)


@driver.on_shutdown
async def shutdown():
    logger.opt(colors=True).info("<y>maimai Prober Shutdown</y>")


from .lib import cmd  # noqa: E402, F401

try:
    import nonebot.adapters.qq  # noqa: F401
    from .lib import qq_official  # noqa: F401
except:
    pass
