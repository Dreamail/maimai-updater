import json

import httpx


class Lxns:
    client: httpx.AsyncClient
    songs: dict

    def __init__(self, token: str):
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": token,
            },
            timeout=30,
        )

    async def create_player(self, name: str, rating: str, friend_code: str):
        resp = await self.client.post(
            "https://maimai.lxns.net/api/v0/maimai/player",
            json={"name": name, "rating": rating, "friend_code": friend_code},
        )
        return resp.json()

    async def get_player(self, friend_code: str):
        resp = await self.client.get(
            f"https://maimai.lxns.net/api/v0/maimai/player/{friend_code}"
        )
        return resp.json()

    async def get_songs(self):
        if not hasattr(self, "songs"):
            resp = await self.client.get(
                "https://maimai.lxns.net/api/v0/maimai/song/list"
            )
            self.songs = resp.json()["songs"]
        return self.songs

    async def title2songid(self, title: str):
        songs = await self.get_songs()
        if (
            title == "Link(CoF)"
        ):  # Special case for Link(CoF) which stands for "Link" in niconico & VOCALOID genre
            return 383
        for song in songs:
            if song["title"] == title:
                return song["id"]
        return None

    async def df2lxns(self, df: str):
        df_records = json.loads(df)
        lx_records = []
        for df_record in df_records:
            songid = await self.title2songid(df_record["title"])
            lx_records.append(
                {
                    "id": songid,
                    "type": "standard" if df_record["type"] == "SD" else "dx",
                    "level_index": df_record["level_index"],
                    "achievements": df_record["achievements"],
                    "fc": df_record["fc"] if df_record["fc"] != "" else None,
                    "fs": df_record["fs"] if df_record["fs"] != "" else None,
                    "dx_score": df_record["dxScore"],
                }
            )
        return {
            "scores": lx_records,
        }

    async def upload_records(self, friend_code: str, records: dict):
        resp = await self.client.post(
            f"https://maimai.lxns.net/api/v0/maimai/player/{friend_code}/scores",
            json=records,
        )

        return resp.json()
