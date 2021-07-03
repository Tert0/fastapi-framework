from typing import Union, List
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi import HTTPException, FastAPI
from sqlalchemy import Column, String, Integer

from fastapi_framework.database import select, filter_by, exists, delete, db

from httpx import AsyncClient, Response

app = FastAPI()


class User(db.Base):
    __tablename__ = "users"
    id: Union[Column, int] = Column(Integer, primary_key=True)
    name: Union[Column, str] = Column(String(255))

    @staticmethod
    async def create(name: str) -> "User":
        row = User(name=name)
        await db.add(row)
        return row


@app.get("/users")
async def get_users():
    return await db.all(select(User))


@app.get("/users/{name}")
async def get_users(name: str):
    return await db.all(select(User).filter_by(name=name))


@app.post("/users/{name}")
async def add_user(name: str) -> User:
    if await db.exists(select(User).filter_by(name=name)):
        raise HTTPException(409, "Username already used")
    user = await User.create(name)
    await db.commit()
    return user


class TestDatabase(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await db.create_tables()

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

    @patch("fastapi_framework.database.db._session")
    async def test_add_row(self, async_session_patch: AsyncMock):
        row = MagicMock()
        await db.add(row)
        async_session_patch.add.assert_called_with(row)

    async def test_get_users(self):
        async with AsyncClient(app=app, base_url="https://test") as ac:
            response: Response = await ac.get("/users")
        self.assertIsInstance(response.json(), List)
