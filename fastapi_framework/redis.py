from aioredis import Redis, create_redis_pool, create_redis
from dotenv import load_dotenv
from os import getenv

from fastapi_framework.modules import disabled_modules

load_dotenv()

REDIS_HOST = getenv("REDIS_HOST", "localhost")
REDIS_PORT = getenv("REDIS_PORT", "6379")


class RedisDependency:
    """FastAPI Dependency for Redis Connections"""

    redis: Redis = None

    def __call__(self):
        return self.redis

    async def init(self):
        """Initialises the Redis Dependency"""
        if "redis" in disabled_modules:
            raise Exception("Module Redis is disabled")
        self.redis: Redis = await create_redis_pool(f"redis://{REDIS_HOST}:{REDIS_PORT}")


redis_dependency: RedisDependency = RedisDependency()


async def get_redis() -> Redis:
    """Returns a NEW Redis connection"""
    if "redis" in disabled_modules:
        raise Exception("Module Redis is disabled")
    return await create_redis(f"redis://{REDIS_HOST}:{REDIS_PORT}")
