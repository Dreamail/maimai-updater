from typing import Optional

from pydantic import BaseModel


class Config(BaseModel):
    super_group: Optional[str] = None
    super_guild: Optional[str] = None
    super_channel: Optional[str] = None
    super_guild_users: Optional[list[str]] = None

    # strict mode
    # 0: disable
    # 1: fetch only win and only lose
    # 2: fetch all
    strict: Optional[int] = 0

    lxns_token: Optional[str] = None

    class Config:
        extra = "ignore"
        coerce_numbers_to_str = True
