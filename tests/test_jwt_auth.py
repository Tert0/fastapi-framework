from datetime import timedelta, datetime
from typing import Dict, Union, List
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock

import jwt
from aioredis import Redis
from fastapi import FastAPI, Depends, HTTPException
from httpx import AsyncClient, Response

from fastapi_framework import redis_dependency
from fastapi_framework.jwt_auth import (
    get_token,
    create_jwt_token,
    ALGORITHM,
    get_data,
    create_access_token,
    create_refresh_token,
    invalidate_refresh_token,
    check_refresh_token,
    generate_tokens,
)

app = FastAPI()

users: List[Dict[str, Union[str, int]]] = [
    {"user_id": 1, "username": "test", "password": "123"},
    {"user_id": 2, "username": "admin", "password": "AdminPassword"},
]


@app.get("/token")
async def token_route(username: str, password: str, redis: Redis = Depends(redis_dependency)):
    user: Union[Dict[str, Union[str, int]], None] = None
    for user_item in users:
        if user_item["username"] == username:
            user = user_item.copy()  # noqa
            break

    if (user is None) or password != user["password"]:
        raise HTTPException(401, detail="Username or Password is wrong")
    return await generate_tokens(
        {"user": {"id": user["user_id"], "username": user["username"]}}, int(user["user_id"]), redis
    )


@app.get("/refresh")
async def refresh_route(refresh_token: str, redis: Redis = Depends(redis_dependency)):
    data: Dict = {}
    if not await check_refresh_token(refresh_token, redis):
        raise HTTPException(401, "Refresh Token Invalid")
    try:
        data = await get_data(refresh_token)
    except HTTPException as e:
        if e.detail == "Token is expired":
            await invalidate_refresh_token(refresh_token, redis)
            raise e
    user_id = int(data["user_id"])
    username: str = ""
    for user in users:
        if user["user_id"] == user_id:
            username = str(user["username"])
    await invalidate_refresh_token(refresh_token, redis)
    return await generate_tokens({"user": {"id": user_id, "username": username}}, int(user_id), redis)


@app.get("/logout", dependencies=[Depends(get_token)])
async def logout_route(refresh_token: str, redis: Redis = Depends(redis_dependency)):
    await invalidate_refresh_token(refresh_token, redis)


@app.get("/secret", dependencies=[Depends(get_data)])
async def secured_route():
    return "Hello!"


class TestJWTAuth(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await redis_dependency.init()

    async def test_get_token(self):
        bearer_scheme = MagicMock()
        bearer_scheme.credentials = "TEST_JWT_TOKEN"
        self.assertEqual(await get_token(bearer_scheme), "TEST_JWT_TOKEN")

    @patch("fastapi_framework.jwt_auth.SECRET_KEY", "TEST_SECRET_KEY")
    async def test_create_jwt_token(self):
        data = {"test": "test_value"}

        jwt_token = await create_jwt_token(data, timedelta(minutes=30))

        self.assertIsInstance(jwt_token, str)
        decoded_data = jwt.decode(jwt_token, "TEST_SECRET_KEY", algorithms=[ALGORITHM])
        self.assertTrue("test" in decoded_data)
        self.assertTrue("exp" in decoded_data)
        self.assertEqual(decoded_data["test"], data["test"])
        self.assertIsInstance(decoded_data["exp"], int)

    @patch("fastapi_framework.jwt_auth.SECRET_KEY", "TEST_SECRET_KEY")
    async def test_get_data(self):
        data = {"test": "test_value"}

        jwt_token = jwt.encode(data, "TEST_SECRET_KEY", algorithm=ALGORITHM)

        decoded_data = await get_data(jwt_token)
        self.assertIsInstance(decoded_data, Dict)
        self.assertEqual(decoded_data, data)

    @patch("fastapi_framework.jwt_auth.SECRET_KEY", "TEST_SECRET_KEY")
    async def test_get_data_invalid_token(self):
        data = {"exp": datetime.utcnow() - timedelta(minutes=10)}

        jwt_token = jwt.encode(data, "TEST_SECRET_KEY", algorithm=ALGORITHM)

        with self.assertRaises(HTTPException):
            await get_data(jwt_token)

    @patch("fastapi_framework.jwt_auth.SECRET_KEY", "TEST_SECRET_KEY")
    async def test_create_access_token(self):
        data = {"test": "test_value"}

        jwt_token = await create_access_token(data)

        decoded_data = jwt.decode(jwt_token, "TEST_SECRET_KEY", algorithms=[ALGORITHM])
        self.assertTrue("test" in decoded_data)
        self.assertEqual(decoded_data["test"], data["test"])

    @patch("fastapi_framework.jwt_auth.SECRET_KEY", "TEST_SECRET_KEY")
    async def test_create_refresh_token(self):
        user_id: int = 5
        redis = AsyncMock()

        jwt_token = await create_refresh_token(user_id, redis)

        redis.sadd.assert_called_once_with("refresh_tokens", jwt_token)
        decoded_data = jwt.decode(jwt_token, "TEST_SECRET_KEY", algorithms=[ALGORITHM])
        self.assertTrue("user_id" in decoded_data)
        self.assertEqual(decoded_data["user_id"], user_id)

    async def test_invalidate_refresh_token(self):
        redis = AsyncMock()

        await invalidate_refresh_token("TEST_REFRESH_TOKEN", redis)

        redis.srem.assert_called_once_with("refresh_tokens", "TEST_REFRESH_TOKEN")

    async def test_check_refresh_token_positive(self):
        redis = AsyncMock()
        redis.smembers = AsyncMock()
        redis.smembers.return_value = [
            b"TEST_FALSE_REFRESH_TOKEN",
            b"TEST_SECOND_FALSE_REFRESH_TOKEN",
            b"TEST_REFRESH_TOKEN",
        ]

        result = await check_refresh_token("TEST_REFRESH_TOKEN", redis)

        redis.smembers.assert_called_once_with("refresh_tokens")
        self.assertTrue(result)

    async def test_check_refresh_token_negative(self):
        redis = AsyncMock()
        redis.smembers = AsyncMock()
        redis.smembers.return_value = [
            b"TEST_FALSE_REFRESH_TOKEN",
            b"TEST_SECOND_FALSE_REFRESH_TOKEN",
        ]

        result = await check_refresh_token("TEST_REFRESH_TOKEN", redis)

        redis.smembers.assert_called_once_with("refresh_tokens")
        self.assertFalse(result)

    @patch("fastapi_framework.jwt_auth.SECRET_KEY", "TEST_SECRET_KEY")
    async def test_generate_tokens(self):
        data = {"test": "test_value"}
        user_id = 6
        redis = AsyncMock()

        tokens = await generate_tokens(data, user_id, redis)

        self.assertTrue("token_type" in tokens)
        self.assertEqual(tokens["token_type"], "bearer")
        self.assertTrue("access_token" in tokens)
        self.assertTrue("refresh_token" in tokens)
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        redis.sadd.assert_called_once_with("refresh_tokens", refresh_token)
        decoded_access_token = jwt.decode(access_token, "TEST_SECRET_KEY", algorithms=[ALGORITHM])
        self.assertTrue("test" in decoded_access_token)
        self.assertEqual(decoded_access_token["test"], data["test"])
        decoded_refresh_token = jwt.decode(refresh_token, "TEST_SECRET_KEY", algorithms=[ALGORITHM])
        self.assertTrue("user_id" in decoded_refresh_token)
        self.assertEqual(decoded_refresh_token["user_id"], user_id)

    @patch("fastapi_framework.jwt_auth.SECRET_KEY", "TEST_SECRET_KEY")
    async def test_login(self):
        async with AsyncClient(app=app, base_url="https://test") as ac:
            response: Response = await ac.get("/token", params={"username": "test", "password": "123"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue("access_token" in response.json())
        self.assertTrue("refresh_token" in response.json())
        self.assertTrue("token_type" in response.json())
        self.assertEqual(response.json()["token_type"], "bearer")

    @patch("fastapi_framework.jwt_auth.SECRET_KEY", "TEST_SECRET_KEY")
    async def test_login_invalid_credentials(self):
        async with AsyncClient(app=app, base_url="https://test") as ac:
            response: Response = await ac.get("/token", params={"username": "not_exists", "password": "wrong"})

        self.assertEqual(response.status_code, 401)

    @patch("fastapi_framework.jwt_auth.SECRET_KEY", "TEST_SECRET_KEY")
    async def test_secret_route(self):
        async with AsyncClient(app=app, base_url="https://test") as ac:
            response: Response = await ac.get("/token", params={"username": "test", "password": "123"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue("access_token" in response.json())
        self.assertTrue("token_type" in response.json())
        self.assertEqual(response.json()["token_type"], "bearer")
        access_token = response.json()["access_token"]

        async with AsyncClient(app=app, base_url="https://test") as ac:
            response: Response = await ac.get("/secret", headers={"Authorization": f"Bearer {access_token}"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), '"Hello!"')

    @patch("fastapi_framework.jwt_auth.SECRET_KEY", "")
    async def test_empty_secret_key(self):
        from fastapi_framework.jwt_auth import check_secret_key

        with self.assertRaises(Exception):
            check_secret_key()
