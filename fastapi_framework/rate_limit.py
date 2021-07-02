from typing import Union, Callable, Dict, Coroutine

from aioredis import Redis
from fastapi import Request, HTTPException, Response
from fastapi.security import HTTPBearer

from fastapi_framework import get_data
from fastapi_framework.modules import disabled_modules


async def default_callback(headers: Dict):
    """Default Error Callback when get Raid Limited"""
    raise HTTPException(429, detail="Too Many Requests", headers=headers)


async def default_get_uuid(request: Request) -> str:
    """Default getter for UUID working with Users IP"""
    return f"{request.client.host}"


async def get_uuid_user_id(request: Request):
    """Getter for UUID working with User IDs from the JWTs"""
    token: str = (await (HTTPBearer())(request)).credentials
    data: Dict = await get_data(token)
    return f"{data['user_id']}"


class RateLimitManager:
    """Rate Limit Manager for Redis, UUID Getter and the Error Callback"""

    redis: Union[Redis, None] = None
    get_uuid: Union[Callable, Coroutine] = default_get_uuid
    callback: Union[Callable, Coroutine] = default_callback

    @classmethod
    async def init(
        cls,
        redis: Redis,
        get_uuid: Union[Callable, Coroutine] = default_get_uuid,
        callback: Union[Callable, Coroutine] = default_callback,
    ):
        """Initialise Rate Limit Manager"""
        if "rate_limit" in disabled_modules:
            raise Exception("Module Rate Limit is disabled")
        cls.redis = redis
        cls.get_uuid = get_uuid
        cls.callback = callback


class RateLimitTime:
    __milliseconds: int

    def __init__(self, seconds: int = 0, minutes: int = 0, hours: int = 0, days: int = 0):
        self.__milliseconds = (seconds + (minutes * 60) + (hours * 60 * 60) + (days * 60 * 60 * 24)) * 1000

    @property
    def milliseconds(self):
        return self.__milliseconds


class RateLimiter:
    """Raid Limit Dependency"""

    count: int
    time: RateLimitTime
    get_uuid: Union[Callable, Coroutine]
    callback: Union[Callable, Coroutine]

    def __init__(
        self,
        count,
        time: RateLimitTime,
        get_uuid: Union[Callable, Coroutine, None] = None,
        callback: Union[Callable, Coroutine, None] = None,
    ):
        if "rate_limit" in disabled_modules:
            raise Exception("Module Rate Limit is disabled")
        self.time = time
        self.count = count
        self.get_uuid = get_uuid
        self.callback = callback

    async def __call__(self, request: Request, response: Response):
        if not RateLimitManager.redis:
            raise Exception("You have to initialise the RateLimitManager at the Startup")
        self.get_uuid = self.get_uuid or RateLimitManager.get_uuid
        self.callback = self.callback or RateLimitManager.callback
        uuid: Union[str, Coroutine] = self.get_uuid(request)
        if isinstance(uuid, Coroutine):
            uuid: str = await uuid
        redis_key: str = f"rate_limit:{request.url.path}:{uuid}"
        redis_key_lock: str = f"{redis_key}:lock"
        if await RateLimitManager.redis.exists(redis_key_lock):
            headers = await self.get_headers(redis_key)
            result = None
            if isinstance(self.callback, Callable):
                result = self.callback(headers)
            if isinstance(result, Coroutine):
                await result
            return

        count = await RateLimitManager.redis.incr(redis_key)
        if count == 1:
            await RateLimitManager.redis.pexpire(redis_key, self.time.milliseconds)
        if count >= self.count:
            pttl: int = await RateLimitManager.redis.pttl(redis_key)
            await RateLimitManager.redis.delete(redis_key)
            await RateLimitManager.redis.set(redis_key_lock, 1, pexpire=pttl)
        headers = await self.get_headers(redis_key)
        for key in headers.keys():
            response.headers[key] = headers[key]

    async def get_headers(self, redis_key: str) -> Dict:
        """Generates Rate Limit Headers"""
        headers: Dict = {}
        redis_value = await RateLimitManager.redis.get(redis_key)
        redis_value = redis_value if redis_value is None else redis_value.decode("utf-8")
        headers["X-Rate-Limit-Limit"] = f"{self.count}"
        headers["X-Rate-Limit-Remaining"] = str(
            redis_value or (0 if await RateLimitManager.redis.exists(f"{redis_key}:lock") else self.count)
        )
        ttl: int = await RateLimitManager.redis.ttl(redis_key)
        ttl: int = ttl if ttl != -2 else await RateLimitManager.redis.ttl(f"{redis_key}:lock")
        ttl: int = ttl if ttl != -2 else 0
        headers["X-Rate-Limit-Reset"] = f"{ttl}"
        return headers
