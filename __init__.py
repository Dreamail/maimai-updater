import os

from nonebot import get_driver, logger, require

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler  # noqa: E402

driver = get_driver()
data_dir = "data/maimai-prober/"
os.makedirs(data_dir, exist_ok=True)

from .config import Config  # noqa: E402

plugin_config = Config.parse_obj(driver.config)

from .lib import wbot  # noqa: E402


@driver.on_bot_connect
async def init():
    logger.info("init maibot...")
    await wbot.init_wahlap()
    logger.info("check maimai token...")
    await wbot.check_token()
    logger.info("prober init successfully")

    scheduler.add_job(wbot.check_token, "interval", hours=1)


@driver.on_shutdown
async def shutdown():
    logger.opt(colors=True).info("<y>maimai Prober Shutdown</y>")


from .lib import cmd  # noqa: E402, F401
