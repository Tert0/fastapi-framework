from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, AsyncMock

from aioredis import Redis

from fastapi_framework.redis import RedisDependency, get_redis
from fastapi_framework import redis


class TestRedis(IsolatedAsyncioTestCase):
    @patch.object(redis, "disabled_modules", [])
    async def test_redis_dependency_init(self):
        redis_dependency: RedisDependency = RedisDependency()
        self.assertEqual(redis_dependency.redis, None)
        await redis_dependency.init()
        self.assertNotEqual(redis_dependency.redis, None)
        self.assertIsInstance(redis_dependency.redis, Redis)

    @patch.object(redis, "disabled_modules", ["redis"])
    async def test_redis_dependency_init_disabled_redis(self):
        redis_dependency: RedisDependency = RedisDependency()
        self.assertEqual(redis_dependency.redis, None)
        with self.assertRaises(Exception):
            await redis_dependency.init()

    async def test_redis_dependency_call(self):
        redis_dependency: RedisDependency = RedisDependency()
        redis_dependency.redis = MagicMock()
        self.assertEqual(redis_dependency.__call__(), redis_dependency.redis)

    @patch.object(redis, "disabled_modules", [])
    async def test_get_redis(self):
        result = await get_redis()
        self.assertIsInstance(result, Redis)

    @patch.object(redis, "disabled_modules", ["redis"])
    async def test_get_redis_disabled_redis(self):
        with self.assertRaises(Exception):
            await get_redis()
