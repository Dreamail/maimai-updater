import httpx


class Lxns:
    client: httpx.AsyncClient

    def __init__(self, token: str):
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": token,
            },
            timeout=30,
            verify=False
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