# Example

This is a JWT Login/Logout Example with Refresh Tokens.

In this example we're using a Fake DB!

```python
from typing import Dict, Union

from aioredis import Redis
from fastapi import FastAPI, Depends, HTTPException

from fastapi_framework import (
    redis_dependency,
    get_data,
    pwd_context,
    invalidate_refresh_token,
    check_refresh_token,
    get_token,
    generate_tokens,
)

app = FastAPI()

fake_user_db: Dict[int, Dict[str, str]] = {
    0: {
        "id": "0",
        "username": "test",
        "password": "$2b$12$vywwXgt8aHzb8PGhTvkZB.y20PzMfBxPr2i9ljr8QFUY6pe7DGWtG",  # Password is '123'
    },
    1: {
        "id": "1",
        "username": "admin",
        "password": "$2b$12$Uelb/O331cMgXgzdWo6mTO6nM1KS4fULNPzv.lBbEl4QCFQRjNzAi",  # Password is 'admin'
    },
}


@app.on_event("startup")
async def on_startup():
    await redis_dependency.init()


@app.get("/token")
async def token_route(username: str, password: str, redis: Redis = Depends(redis_dependency)):
    user: Union[Dict[str, str], None] = None
    for user_db in fake_user_db.values():
        if user_db["username"] == username:
            user = user_db.copy()
            break
    if user is None or not pwd_context.verify(password, user["password"]):
        raise HTTPException(401, detail="Username or Password is wrong")
    return await generate_tokens({"user": {"id": user["id"], "username": user["username"]}}, int(user["id"]), redis)


@app.get("/refresh")
async def refresh_route(refresh_token: str, redis: Redis = Depends(redis_dependency)):
    data: Dict = {}
    if not await check_refresh_token(refresh_token, redis):
        raise HTTPException(401, "Refresh Token Invalid")
    try:
        data = await get_data(refresh_token)
    except HTTPException as e:
        if e.detail == "Token is expired":
            await invalidate_refresh_token(refresh_token, redis)
            raise e
    user_id = int(data["user_id"])
    user = fake_user_db[user_id]
    await invalidate_refresh_token(refresh_token, redis)
    return await generate_tokens({"user": {"id": user["id"], "username": user["username"]}}, int(user["id"]), redis)


@app.get("/logout")
async def logout_route(refresh_token: str, redis: Redis = Depends(redis_dependency), _=Depends(get_token)):
    await invalidate_refresh_token(refresh_token, redis)


@app.get("/secret")
async def secured_route(data: Dict = Depends(get_data)):
    return f'Hello {data["user"]["username"]}!'

```