# JWT Tokens

There are two types of Tokens:
- Access Token
- Refresh Token

## Access Token

This token saves Data like `User ID`, `Username` and `Permission`.
The User can't modify this without the `JWT_SECRET_KEY`.
The Access Token expires after a short time

## Refresh Token
This Token has a UUID as Data.
With this Token you can Refresh your Tokens and get new Tokens.
The Refresh Token expires after a long time.
It will get Cached in Redis so if you delete it from
Redis the Refresh Token is invalid, and the User have to log in again

## Implementation

### Access Token

```python
from fastapi_framework.jwt_auth import create_access_token
from fastapi import FastAPI

app = FastAPI()


@app.get("/jwt/access_token")
async def get_access_token():
    return await create_access_token(
        {
            "user": {
                "id": 5,
                "username": "test",
                "admin": True,
            }
        }
    )

```

Now you can test the Endpoint, and you'll get a JWT Access Token.
To Debug JWT Tokens you can use [jwt.io](https://jwt.io/#debugger-io)

![img.png](jwt_io_screenshot.png)

### Refresh Tokens

```python
from aioredis import Redis

from fastapi_framework import redis_dependency
from fastapi_framework.jwt_auth import create_refresh_token
from fastapi import FastAPI, Depends

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await redis_dependency.init()


@app.get("/jwt/refresh_token")
async def get_refresh_token(redis: Redis = Depends(redis_dependency)):
    return await create_refresh_token(5, redis)

```

Now you can test the Endpoint, and you'll get a JWT Refresh Token.
The Refresh Token should be in the Redis Cache in the Set `refresh_tokens`

You can check it with the Redis Command `smembers refresh_tokens`

```shell
localhost:63792> smembers refresh_tokens
1) "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo1LCJleHAiOjE2MjQ3OTg2MTN9.YVjN2ElK85Mjq9FL0fteZNGpsag78dm2g2EH9gsXsLE"
localhost:63792>
```

### Both
There is a shorter Way if you want to generate both Tokens e.g. for Login.

```python
from aioredis import Redis

from fastapi_framework import redis_dependency
from fastapi_framework.jwt_auth import generate_tokens
from fastapi import FastAPI, Depends

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await redis_dependency.init()


@app.get("/jwt/")
async def get_tokens(redis: Redis = Depends(redis_dependency)):
    return await generate_tokens(
        {
            "user": {
                "id": 5,
                "username": "test",
                "admin": True,
            }
        },
        5,
        redis,
    )

```

You'll get a Dict with Data like
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjp7ImlkIjo1LCJ1c2VybmFtZSI6InRlc3QiLCJhZG1pbiI6dHJ1ZX0sImV4cCI6MTYyNDc4NjMwOH0.-7ZdW06DguPb5LMjRym7fDLIUoJeBCa1CohTUNPibpE",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo1LCJleHAiOjE2MjQ3OTg5MDh9.vKTwD-pA2S63MPQ3g42a-wIxl7-QcUzSjwtRXI_X_wE",
  "token_type": "bearer"
}
```

### Logout

To Logout a use you should invalidate the Refresh Token
```python
from aioredis import Redis

from fastapi_framework import redis_dependency
from fastapi_framework.jwt_auth import invalidate_refresh_token
from fastapi import FastAPI, Depends

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await redis_dependency.init()


@app.get("/logout/")
async def logout(refresh_token: str, redis: Redis = Depends(redis_dependency)):
    await invalidate_refresh_token(refresh_token, redis)
    return None

```

Now you can check out the `refresh_tokens` Set in Redis.
The Refresh Token should be deleted now.

```shell
localhost:63792> smembers refresh_tokens
1) "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo1LCJleHAiOjE2MjQ3OTg5MDh9.vKTwD-pA2S63MPQ3g42a-wIxl7-QcUzSjwtRXI_X_wE"
localhost:63792>

# After the Logout

localhost:63792> smembers refresh_tokens
(empty list or set)
localhost:63792>
```

### Check Refresh Token

In the Refresh Route you have to check if the Token is in the Redis Cache

```python
from aioredis import Redis

from fastapi_framework import redis_dependency
from fastapi_framework.jwt_auth import check_refresh_token
from fastapi import FastAPI, Depends

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await redis_dependency.init()


@app.get("/check_token/")
async def check_token(refresh_token: str, redis: Redis = Depends(redis_dependency)):
    return await check_refresh_token(refresh_token, redis)

```

### Get Users Token
If you want to get the Access
Token from the User you can do
that with the FastAPI Dependency `fastapi_framework.get_token`.

```python
from fastapi import FastAPI, Depends

from fastapi_framework.jwt_auth import get_token

app = FastAPI()


@app.get("/get_token/")
async def check_token(token: str = Depends(get_token)):
    return token

```

**Note: To implement the 
Authentication in the Client send
a `Authorization` Header with `Bearer <jwt-access-token-here>`**

### Get JWT Tokens Data (as Dependency)

To get the Data from the JWT Token you can use the Dependency
```python
from typing import Dict

from fastapi import FastAPI, Depends

from fastapi_framework.jwt_auth import get_data

app = FastAPI()


@app.get("/get_data/")
async def get_data(data: Dict = Depends(get_data)):
    return data

```

### Get JWT Token Data (with Token)

To get Tokens Data without the Dependency you can use the same function

```python
from fastapi import FastAPI

from fastapi_framework.jwt_auth import get_data

app = FastAPI()


@app.get("/get_data/")
async def get_data(token: str):
    return await get_data(token)

```

