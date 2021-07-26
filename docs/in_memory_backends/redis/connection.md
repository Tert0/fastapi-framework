# Redis Connection

You have to init the redis connection with `await redis_dependency.init()`.

Now you can use it as FastAPI Dependency.

```python
from aioredis import Redis
from fastapi_framework import redis_dependency
from fastapi import FastAPI, Depends

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await redis_dependency.init()


@app.get("/set/{key}/{value}")
async def test(key: str, value: str, redis: Redis = Depends(redis_dependency)):
    await redis.set(key, value)
    return "Done"

```