from typing import Optional

from pydantic import BaseModel


class Config(BaseModel):
    super_guild: Optional[str] = None
    super_channel: Optional[str] = None
    super_guild_users: Optional[list[str]] = None

    class Config:
        extra = "ignore"