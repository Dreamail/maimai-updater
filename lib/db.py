from nonebot.adapters import Event
from nonebot.params import Depends
from nonebot_plugin_orm import Model
from sqlalchemy.orm import Mapped, mapped_column


class Token(Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str]
    userid: Mapped[str]


def get_user_id(event: Event) -> str:
    return event.get_user_id()


class User(Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = Depends(get_user_id)
    friend_id: Mapped[str]
    df_token: Mapped[str]
