from typing import Optional

from pydantic import BaseModel


class Config(BaseModel):
    super_group: Optional[str] = None
    super_guild: Optional[str] = None
    super_channel: Optional[str] = None
    super_guild_users: Optional[list[str]] = None

    strict: Optional[int] = 0

    class Config:
        extra = "ignore"
