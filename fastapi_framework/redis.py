from aioredis import Redis, create_redis_pool
from dotenv import load_dotenv
from os import getenv

load_dotenv()

REDIS_HOST = getenv("REDIS_HOST", "localhost")
REDIS_PORT = getenv("REDIS_PORT")


class RedisDependency:
    redis: Redis = None

    def __call__(self):
        return self.redis

    async def init(self):
        self.redis: Redis = await create_redis_pool(f'redis://{REDIS_HOST}:{REDIS_PORT}')


redis_dependency: RedisDependency = RedisDependency()


async def get_redis() -> Redis:
    return await create_redis_pool(f'redis://{REDIS_HOST}:{REDIS_PORT}')
