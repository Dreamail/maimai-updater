import asyncio
from contextvars import copy_context
from functools import partial
from typing import Optional

import httpx

from maimai_pageparser import ParseRecords
from .wahlap import Wahlap
from .lxns import Lxns

DIFF = ["Basic", "Advanced", "Expert", "Master", "Re:Master"]


class UploadError(Exception): ...  # TODO: distinguish between df and lxns upload errors


async def parse_page(achievementsvs: str, dxscorevs: str, diff: int) -> str:
    loop = asyncio.get_running_loop()
    pfunc = partial(ParseRecords, achievementsvs, dxscorevs, diff)
    context = copy_context()

    try:
        return await loop.run_in_executor(None, partial(context.run, pfunc))
    except RuntimeError as e:
        if str(e) != "record was not found":
            raise e


async def upload_df_records(token: str, records: str):
    resp = await httpx.AsyncClient(timeout=15).post(
        "https://www.diving-fish.com/api/maimaidxprober/player/update_records",
        data=records,  # due to the parser wrote in golang, i have to post raw json str
        headers={"Import-Token": token, "Content-Type": "application/json"},
    )

    if resp.status_code != 200:
        if hasattr(resp.json, "message"):
            raise UploadError(resp.json.message)
        raise UploadError("status_code: " + str(resp.status_code))


async def upload_lxns_records(lx: Lxns, friend_code: str, records: str):
    records = await lx.df2lxns(records)
    if records == []:
        raise UploadError("Cannot convert df records to lxns records")

    resp = await lx.upload_records(friend_code, records)

    if resp["code"] != 200:
        if "message" in resp:
            raise UploadError(resp["message"])
        raise UploadError("status_code: " + str(resp["code"]))


async def update_score(
    wl: Wahlap,
    lx: Optional[Lxns],
    token: str,
    friend_code: str,
    diff: int,
    update_df: bool,
    update_lx: bool,
    strict: int = 0,
):
    tasks = [
        wl.get_friend_vs(friend_code, 0, diff, only_lose=(strict <= 1)),
        wl.get_friend_vs(friend_code, 1, diff, only_lose=(strict <= 1)),
    ]
    if strict == 1:
        tasks.extend(
            [
                wl.get_friend_vs(friend_code, 0, diff, only_win=True),
                wl.get_friend_vs(friend_code, 1, diff, only_win=True),
            ]
        )
        avs, dvs, avs2, dvs2 = await asyncio.gather(*tasks)
        records = await parse_page(avs2, dvs2, diff)
        if records:
            upload_tasks = []
            if update_df:
                upload_tasks.append(upload_df_records(token, records))
            if update_lx and lx is not None:
                upload_tasks.append(upload_lxns_records(lx, friend_code, records))
            await asyncio.gather(*upload_tasks)

    else:
        avs, dvs = await asyncio.gather(*tasks)

    records = await parse_page(avs, dvs, diff)
    if records:
        upload_tasks = []
        if update_df:
            upload_tasks.append(upload_df_records(token, records))
        if update_lx and lx is not None:
            upload_tasks.append(upload_lxns_records(lx, friend_code, records))
        await asyncio.gather(*upload_tasks)
