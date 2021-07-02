from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from fastapi_framework.rate_limit import (
    RateLimitManager,
    RateLimiter,
    RateLimitTime,
    default_get_uuid,
    default_callback,
)
from fastapi_framework import rate_limit


class TestRateLimit(IsolatedAsyncioTestCase):
    async def test_rate_limit_manager_init(self):
        redis = AsyncMock()
        await RateLimitManager.init(redis)
        self.assertEqual(RateLimitManager.redis, redis)
        self.assertEqual(RateLimitManager.callback, default_callback)
        self.assertEqual(RateLimitManager.get_uuid, default_get_uuid)

    async def test_rate_limit_time(self):
        rate_limit_time = RateLimitTime(seconds=100)
        self.assertEqual(rate_limit_time.milliseconds, 100 * 1000)
        rate_limit_time = RateLimitTime(minutes=3)
        self.assertEqual(rate_limit_time.milliseconds, 3 * 60 * 1000)
        rate_limit_time = RateLimitTime(hours=2)
        self.assertEqual(rate_limit_time.milliseconds, 2 * 60 * 60 * 1000)
        rate_limit_time = RateLimitTime(days=5)
        self.assertEqual(rate_limit_time.milliseconds, 5 * 24 * 60 * 60 * 1000)

    @patch.object(rate_limit, "disabled_modules", [])
    async def test_rate_limiter_init(self):
        count = 5
        time = RateLimitTime(seconds=56)
        rate_limiter = RateLimiter(count, time)
        self.assertEqual(rate_limiter.count, count)
        self.assertEqual(rate_limiter.time, time)
        self.assertEqual(rate_limiter.get_uuid, None)
        self.assertEqual(rate_limiter.callback, None)

    @patch.object(rate_limit, "disabled_modules", ["rate_limit"])
    async def test_rate_limiter_init_disabled(self):
        count = 5
        time = RateLimitTime(seconds=56)
        self.assertRaises(Exception, RateLimiter.__init__, count, time)
