from datetime import timedelta
from typing import Dict
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock
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
import jwt


class TestJWTAuth(IsolatedAsyncioTestCase):
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
    async def test_create_access_token(self):
        data = {"test": "test_value"}
        jwt_token = await create_access_token(data)
        decoded_data = jwt.decode(jwt_token, "TEST_SECRET_KEY", algorithms=[ALGORITHM])
        self.assertTrue("test" in decoded_data)
        self.assertEqual(decoded_data["test"], data["test"])

    @patch("fastapi_framework.jwt_auth.SECRET_KEY", "TEST_SECRET_KEY")
    async def test_create_refresh_token(self):
        user_id: int = 5
        redis = MagicMock()
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
        redis = MagicMock()
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

