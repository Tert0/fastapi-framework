from typing import Union, Callable, Dict, Coroutine

from aioredis import Redis
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from fastapi_framework import get_data


def default_callback():
    raise HTTPException(429, detail="You got Raid Limited")


def default_get_uuid(request: Request) -> str:
    return f"{request.client.host}"


async def get_uuid_user_id(request: Request):
    token: str = (await (HTTPBearer())(request)).credentials
    data: Dict = await get_data(token)
    return f"{data['user_id']}"


class RateLimitManager:
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
        cls.redis = redis
        cls.get_uuid = get_uuid
        cls.callback = callback


class RateLimiter:
    count: int
    milliseconds: int
    get_uuid: Union[Callable, Coroutine]
    callback: Union[Callable, Coroutine]

    def __init__(
        self,
        count,
        milliseconds: int = 0,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        days: int = 0,
        get_uuid: Union[Callable, Coroutine, None] = None,
        callback: Union[Callable, Coroutine, None] = None,
    ):
        self.milliseconds = milliseconds + (seconds + (minutes * 60) + (hours * 60 * 60) + (days * 60 * 60 * 24)) * 1000
        self.count = count
        self.get_uuid = get_uuid
        self.callback = callback

    async def __call__(self, request: Request):
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
            if isinstance(self.callback, Callable):
                self.callback()
            elif isinstance(self.callback, Coroutine):
                await self.callback
            return

        count = await RateLimitManager.redis.incr(redis_key)
        if count == 1:
            await RateLimitManager.redis.pexpire(redis_key, self.milliseconds)
        if count >= self.count:
            pttl: int = await RateLimitManager.redis.pttl(redis_key)
            await RateLimitManager.redis.delete(redis_key)
            await RateLimitManager.redis.set(redis_key_lock, 1, pexpire=pttl)
