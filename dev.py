import nonebot
from nonebot.adapters.qq import Adapter as QQAdapter
from nonebot.adapters.onebot import V11Adapter as OneBotAdapter


def main():
    nonebot.init()

    driver = nonebot.get_driver()
    driver.register_adapter(QQAdapter)
    driver.register_adapter(OneBotAdapter)
    nonebot.load_plugin("nonebot_plugin_maimai_updater")

    nonebot.run()


if __name__ == "__main__":
    main()
