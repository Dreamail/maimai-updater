from typing import Annotated, TypeAlias

from nonebot.adapters import Event
from nonebot.params import Depends
from nonebot_plugin_orm import Model, get_session
from sqlalchemy import select
from sqlalchemy.orm import Mapped, mapped_column


class Token(Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str]
    userid: Mapped[str]


class User(Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str]
    friend_id: Mapped[str]
    df_token: Mapped[str]

    @classmethod
    async def from_info(cls, user_id: str):
        """Get user model by user info"""
        sql = select(cls).where(cls.user_id == user_id)
        async with get_session() as session:
            result = await session.execute(sql)
            return result.scalar_one_or_none()


async def get_user(event: Event) -> User | None:
    """Get current database user from event."""
    return await User.from_info(event.get_user_id())


USER: TypeAlias = Annotated[User | None, Depends(get_user)]
"""Current database user from event. None if never authenticated."""
