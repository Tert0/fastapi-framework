from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi_framework.redis import RedisDependency, get_redis, RedisBackend
from fastapi_framework import redis


class TestRedis(IsolatedAsyncioTestCase):
    @patch.object(redis, "disabled_modules", [])
    async def test_redis_dependency_init(self):
        redis_dependency: RedisDependency = RedisDependency()
        self.assertEqual(redis_dependency.redis, None)
        await redis_dependency.init()
        self.assertNotEqual(redis_dependency.redis, None)
        self.assertIsInstance(redis_dependency.redis, RedisBackend)

    @patch.object(redis, "disabled_modules", ["redis"])
    async def test_redis_dependency_init_disabled_redis(self):
        redis_dependency: RedisDependency = RedisDependency()
        self.assertEqual(redis_dependency.redis, None)
        with self.assertRaises(Exception):
            await redis_dependency.init()

    async def test_redis_dependency_call(self):
        redis_dependency: RedisDependency = RedisDependency()
        redis_dependency.redis = MagicMock()
        self.assertEqual(await redis_dependency.__call__(), redis_dependency.redis)

    @patch.object(redis, "disabled_modules", [])
    async def test_get_redis(self):
        result = await get_redis()
        self.assertIsInstance(result, RedisBackend)

    @patch.object(redis, "disabled_modules", ["redis"])
    async def test_get_redis_disabled_redis(self):
        with self.assertRaises(Exception):
            await get_redis()

    @patch.object(redis, "disabled_modules", [])
    async def test_expire(self):
        redis_backend = RedisBackend()
        redis_backend.redis_connection = AsyncMock()
        await redis_backend.expire("test", 5000)
        redis_backend.redis_connection.expire.assert_called_with("test", 5000)

    @patch.object(redis, "disabled_modules", [])
    async def test_decrease(self):
        redis_backend = RedisBackend()
        redis_backend.redis_connection = AsyncMock()
        await redis_backend.decr("test")
        redis_backend.redis_connection.decr.assert_called_with("test")

    @patch.object(redis, "disabled_modules", [])
    async def test_smembers(self):
        redis_backend = RedisBackend()
        redis_backend.redis_connection = AsyncMock()
        await redis_backend.smembers("test")
        redis_backend.redis_connection.smembers.assert_called_with("test")

    @patch.object(redis, "disabled_modules", [])
    async def test_sadd(self):
        redis_backend = RedisBackend()
        redis_backend.redis_connection = AsyncMock()
        await redis_backend.sadd("test", "test_value")
        redis_backend.redis_connection.sadd.assert_called_with("test", "test_value")

    @patch.object(redis, "disabled_modules", [])
    async def test_srem(self):
        redis_backend = RedisBackend()
        redis_backend.redis_connection = AsyncMock()
        await redis_backend.srem("test", "test_value")
        redis_backend.redis_connection.srem.assert_called_with("test", "test_value")
