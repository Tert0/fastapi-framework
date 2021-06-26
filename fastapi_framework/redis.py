from aioredis import Redis, create_redis_pool
from asyncio import get_event_loop
from dotenv import load_dotenv
from os import getenv
load_dotenv()

loop = get_event_loop()
REDIS_HOST = getenv("REDIS_HOST")
REDIS_PORT = getenv("REDIS_PORT")
redis: Redis = loop.run_until_complete(create_redis_pool(f''))
