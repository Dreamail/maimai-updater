from typing import Annotated, Optional, TypeAlias

from nonebot.adapters import Event
from nonebot.params import Depends
from nonebot_plugin_orm import Model, SQLDepends
from sqlalchemy import select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio.session import AsyncSession


class Token(Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str]
    userid: Mapped[str]


class User(Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str]
    sec_id: Mapped[Optional[str]]
    magic_id: Mapped[Optional[str]]
    friend_id: Mapped[str]
    df_token: Mapped[Optional[str]]
    prober_type: Mapped[Optional[int]] = mapped_column(
        default=0
    )  # 0: diving fish, 1: lxns
    update_times: Mapped[Optional[int]]

    @classmethod
    async def from_id(cls, id: str, sess: AsyncSession):
        sql = select(cls).where((cls.user_id == id) | (cls.sec_id == id))
        result = await sess.execute(sql)
        return result.scalar_one_or_none()


async def get_user_id(event: Event) -> str:
    return event.get_user_id()


USER: TypeAlias = Annotated[
    User | None,
    SQLDepends(
        select(User).where(
            (User.user_id == Depends(get_user_id))
            | (User.sec_id == Depends(get_user_id))
        )
    ),
]


async def get_all_update_times(sess: AsyncSession) -> int:
    result = (await sess.execute(select(User.update_times))).fetchall()
    times = 0
    for t in result:
        if t[0]:
            times += t[0]

    return times
