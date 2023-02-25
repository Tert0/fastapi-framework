from os import getenv
from typing import Union, List, Dict
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch

from fastapi import HTTPException, FastAPI, Depends
from pydantic import BaseModel, constr, conint
from sqlalchemy import Column, String, Integer

from fastapi_framework.database import (
    select,
    filter_by,
    exists,
    delete,
    database_dependency,
    DB,
    DatabaseDependency,
    Base,
)

from httpx import AsyncClient, Response
from random import choices
from string import ascii_letters

app = FastAPI()


class User(Base):
    __tablename__ = "users"
    id: Union[Column, int] = Column(Integer, primary_key=True)
    name: Union[Column, str] = Column(String(255), unique=True)

    @staticmethod
    async def create(name: str) -> "User":
        db: DB = await database_dependency()
        row = User(name=name)
        await db.add(row)
        return row

    def to_pydantic_user(self) -> "PydanticUser":
        return PydanticUser(id=self.id, name=self.name)


class PydanticUser(BaseModel):
    id: int
    name: constr(max_length=255)


@app.get("/users")
async def get_users(db: DB = Depends(database_dependency)) -> List[PydanticUser]:
    return list(map(User.to_pydantic_user, await db.all(select(User))))


@app.get("/users/{name}")
async def get_user_by_name(name: str, db: DB = Depends(database_dependency)) -> PydanticUser:
    return (await db.first(select(User).filter_by(name=name))).to_pydantic_user()


@app.post("/users/{name}")
async def add_user(name: str, db: DB = Depends(database_dependency)) -> PydanticUser:
    if await db.exists(select(User).filter_by(name=name)):
        raise HTTPException(409, "Username already used")
    user = await User.create(name)
    await db.commit()
    return user.to_pydantic_user()


@app.delete("/users/{name}")
async def remove_user(name: str, db: DB = Depends(database_dependency)):
    query = select(User).filter_by(name=name)
    if not await db.exists(query):
        raise HTTPException(404, "User doesn't exists")
    await db.delete(await db.first(query))
    return True


class TestDatabase(IsolatedAsyncioTestCase):
    @patch("fastapi_framework.database.sa_select")
    async def test_select(self, sa_select: MagicMock):
        model = MagicMock()

        result = select(model)

        sa_select.assert_called_with(model)
        self.assertEqual(result, sa_select())

    @patch("fastapi_framework.database.select")
    async def test_filter_by(self, select_patch: MagicMock):
        model = MagicMock()
        filters = {
            "param1": MagicMock(),
            "param2": MagicMock(),
            "param3": MagicMock(),
            "param4": MagicMock(),
            "param5": MagicMock(),
        }

        result = filter_by(model, **filters)

        select_patch.assert_called_once_with(model)
        select_patch().filter_by.assert_called_once_with(**filters)
        self.assertEqual(select_patch().filter_by(), result)

    @patch("fastapi_framework.database.sa_exists")
    async def test_exists(self, sa_exists: MagicMock):
        model = MagicMock()
        filters = {
            "param1": MagicMock(),
            "param2": MagicMock(),
            "param3": MagicMock(),
            "param4": MagicMock(),
            "param5": MagicMock(),
        }

        result = exists(model, **filters)

        sa_exists.assert_called_once_with(model, **filters)
        self.assertEqual(result, sa_exists())

    @patch("fastapi_framework.database.sa_delete")
    async def test_delete(self, sa_delete: MagicMock):
        model = MagicMock()

        result = delete(model)

        sa_delete.assert_called_once_with(model)
        self.assertEqual(result, sa_delete())

    async def test_add_row(self):
        row = MagicMock()
        db: DB = DB(getenv("DB_DRIVER", "postgresql+asyncpg"), {})
        db._session.add = MagicMock()

        await db.add(row)

        db._session.add.assert_called_with(row)

    async def test_get_users(self):
        async with AsyncClient(app=app, base_url="https://test") as ac:
            response: Response = await ac.get("/users")

        self.assertIsInstance(response.json(), List)

    async def test_add_user(self):
        username = "".join(choices(ascii_letters, k=100))

        async with AsyncClient(app=app, base_url="https://test") as ac:
            response: Response = await ac.post(f"/users/{username}")

        self.assertEqual(response.status_code, 200)
        self.assertTrue("name" in response.json())
        self.assertTrue("id" in response.json())
        self.assertEqual(response.json()["name"], username)
        self.assertIsInstance(response.json()["id"], int)

    async def test_add_user_already_exists(self):
        username = "".join(choices(ascii_letters, k=100))

        async with AsyncClient(app=app, base_url="https://test") as ac:
            response: Response = await ac.post(f"/users/{username}")
            response2: Response = await ac.post(f"/users/{username}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response2.status_code, 409)

    async def test_get_user_by_name(self):
        username = "".join(choices(ascii_letters, k=100))

        async with AsyncClient(app=app, base_url="https://test") as ac:
            await ac.post(f"/users/{username}")
        async with AsyncClient(app=app, base_url="https://test") as ac:
            response: Response = await ac.get(f"/users/{username}")

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(PydanticUser.parse_obj(response.json()), PydanticUser)

    async def test_remove_user(self):
        username = "".join(choices(ascii_letters, k=100))

        async with AsyncClient(app=app, base_url="https://test") as ac:
            response: Response = await ac.post(f"/users/{username}")

        self.assertEqual(response.status_code, 200)

        async with AsyncClient(app=app, base_url="https://test") as ac:
            response = await ac.delete(f"/users/{username}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), "true")

    async def test_remove_user_not_exists(self):
        async with AsyncClient(app=app, base_url="https://test") as ac:
            response: Response = await ac.delete("/users/this_username_dont_exists")

        self.assertEqual(response.status_code, 404)

    async def test_initialise_database_multiple_time(self):
        await database_dependency.init()
        await database_dependency.init()

        self.assertEqual(database_dependency.initialised, True)

    async def test_database_count(self):
        db: DB = await database_dependency()

        user_count: int = await db.count(select(User))
        users: List[Dict] = await db.all(select(User))

        self.assertEqual(len(users), user_count)

    async def test_create_tables(self):
        db: DB = await database_dependency()

        await db.create_tables()

    @patch("fastapi_framework.database.DB_POOL", False)
    async def test_init_database_dependency_without_pool(self):
        DatabaseDependency()
