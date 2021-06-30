# Example
## Example with JWT
```python
from fastapi import FastAPI, Depends


from fastapi_framework import (
    redis_dependency,
    RateLimiter,
    RateLimitManager,
    create_access_token,
    get_uuid_user_id,
    get_data,
    RateLimitTime,
)

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await redis_dependency.init()
    await RateLimitManager.init(await redis_dependency(), get_uuid=get_uuid_user_id)


@app.get("/login")
async def login_route(user_id: int):
    return await create_access_token({"user_id": user_id})


@app.get("/limited", dependencies=[Depends(RateLimiter(2, RateLimitTime(seconds=10))), Depends(get_data)])
async def limited_route():
    return f"Got it"

```

## Example without JWT
```python
from fastapi import FastAPI, Depends


from fastapi_framework import (
    redis_dependency,
    RateLimiter,
    RateLimitManager,
    RateLimitTime
)

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await redis_dependency.init()
    await RateLimitManager.init(await redis_dependency())


@app.get("/limited", dependencies=[Depends(RateLimiter(2, RateLimitTime(seconds=10)))])
async def limited_route():
    return f"Got it"

```