from typing import Set, Any, Optional

from aioredis import create_redis_pool
from aioredis import Redis as RedisConnection
from dotenv import load_dotenv
from os import getenv
from .in_memory_backend import InMemoryBackend, RAMBackend

from .modules import disabled_modules

load_dotenv()

Redis = InMemoryBackend

REDIS_HOST = getenv("REDIS_HOST", "localhost")
REDIS_PORT = getenv("REDIS_PORT", "6379")


class RedisBackend(InMemoryBackend):
    redis_connection: RedisConnection

    @staticmethod
    async def init(url: str) -> "RedisBackend":
        redis = RedisBackend()
        redis.redis_connection = await create_redis_pool(url)
        return redis

    async def get(self, key: str):
        """Get Value from Key"""
        return await self.redis_connection.get(key)

    async def set(self, key: str, value, expire: int = 0, pexpire: int = 0, exists=None):
        """Set Key to Value"""
        return await self.redis_connection.set(key, value, expire=expire, pexpire=pexpire, exist=exists)

    async def pttl(self, key: str) -> int:
        """Get PTTL from a Key"""
        return int(await self.redis_connection.pttl(key))

    async def ttl(self, key: str) -> int:
        """Get TTL from a Key"""
        return int(await self.redis_connection.ttl(key))

    async def pexpire(self, key: str, pexpire: int) -> bool:
        """Sets and PTTL for a Key"""
        return bool(await self.redis_connection.pexpire(key, pexpire))

    async def expire(self, key: str, expire: int) -> bool:
        """Sets and TTL for a Key"""
        return bool(await self.redis_connection.expire(key, expire))

    async def incr(self, key: str) -> int:
        """Increases an Int Key"""
        return int(await self.redis_connection.incr(key))

    async def decr(self, key: str) -> int:
        """Decreases an Int Key"""
        return int(await self.redis_connection.decr(key))

    async def delete(self, key: str):
        """Delete value of a Key"""
        return await self.redis_connection.delete(key)

    async def smembers(self, key: str) -> Set:
        """Gets Set Members"""
        return set(await self.redis_connection.smembers(key))

    async def sadd(self, key: str, value: Any) -> bool:
        """Adds a Member to a Dict"""
        return bool(await self.redis_connection.sadd(key, value))

    async def srem(self, key: str, member: Any) -> bool:
        """Removes a Member from a Set"""
        return bool(await self.redis_connection.srem(key, member))

    async def exists(self, key: str) -> bool:
        """Checks if a Key exists"""
        return bool(await self.redis_connection.exists(key))


class RedisDependency:
    """FastAPI Dependency for Redis Connections"""

    redis: Optional[InMemoryBackend] = None

    async def __call__(self):
        if self.redis is None:
            await self.init()
        return self.redis

    async def init(self):
        """Initialises the Redis Dependency"""
        if "redis" in disabled_modules:
            self.redis = RAMBackend()
        else:
            self.redis = await RedisBackend.init(f"redis://{REDIS_HOST}:{REDIS_PORT}")


redis_dependency: RedisDependency = RedisDependency()


async def get_redis() -> RedisBackend:
    """Returns a NEW Redis connection"""
    if "redis" in disabled_modules:
        raise Exception("Module Redis is disabled")
    return await RedisBackend.init(f"redis://{REDIS_HOST}:{REDIS_PORT}")
