from peewee import Model, TextField
from peewee_async import Manager

from .. import data_dir
from .asnyc_sqlite import SqliteDatabase

db = SqliteDatabase(data_dir + "database.sqlite")
objects = Manager(db)


class BaseModel(Model):
    class Meta:
        database = db


class Token(BaseModel):
    token = TextField()
    userid = TextField()


class User(BaseModel):
    imid = TextField(primary_key=True)
    maimai_id = TextField(null=True)
    token = TextField(null=True)


db.create_tables([Token, User])


async def get_or_create_user(imid: str) -> User:
    return (await objects.get_or_create(User, imid=imid))[0]


async def update_user(user: User):
    await objects.update(user)


async def get_token() -> tuple[str, str]:
    obj = await objects.get_or_none(Token, id=0)  # TODO multi bot support
    if not obj:
        return
    return obj.token, obj.userid


async def save_token(token: str, userid: str):
    obj, exist = await objects.get_or_create(
        Token, {"token": token, "userid": userid}, id=0
    )
    if not exist:
        obj.token = token
        obj.userid = userid
        await objects.update(obj)
