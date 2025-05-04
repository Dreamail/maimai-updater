import asyncio
from contextvars import copy_context
from functools import partial

import httpx

from pageparser import ParseRecords
from .wahlap import Wahlap

DIFF = ["Basic", "Advanced", "Expert", "Master", "Re:Master"]


class UploadError(Exception):
    ...


async def parse_page(achievementsvs: str, dxscorevs: str, diff: int) -> str:
    loop = asyncio.get_running_loop()
    pfunc = partial(ParseRecords, achievementsvs, dxscorevs, diff)
    context = copy_context()

    try:
        return await loop.run_in_executor(None, partial(context.run, pfunc))
    except RuntimeError as e:
        if str(e) != "record was not found":
            raise e


async def upload_records(token: str, records: str):
    resp = await httpx.AsyncClient(timeout=15).post(
        "https://www.diving-fish.com/api/maimaidxprober/player/update_records",
        data=records,  # due to the parser wrote in golang, i have to post raw json str
        headers={"Import-Token": token, "Content-Type": "application/json"},
    )

    if resp.status_code != 200:
        if hasattr(resp.json, "message"):
            raise UploadError(resp.json.message)
        raise UploadError("status_code: " + str(resp.status_code))


async def update_score(wl: Wahlap, token: str, idx: str, diff: int, strict: int = 0):
    tasks = [
        wl.get_friend_vs(idx, 0, diff, only_lose=(strict <= 1)),
        wl.get_friend_vs(idx, 1, diff, only_lose=(strict <= 1)),
    ]
    if strict == 1:
        tasks.extend(
            [
                wl.get_friend_vs(idx, 0, diff, only_win=True),
                wl.get_friend_vs(idx, 1, diff, only_win=True),
            ]
        )
        avs, dvs, avs2, dvs2 = await asyncio.gather(*tasks)
        records = await parse_page(avs2, dvs2, diff)
        if records:
            await upload_records(token, records)

    else:
        avs, dvs = await asyncio.gather(*tasks)

    records = await parse_page(avs, dvs, diff)
    if records:
        await upload_records(token, records)
