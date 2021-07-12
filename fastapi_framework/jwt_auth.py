from datetime import datetime, timedelta
from os import getenv
from typing import Dict

import jwt
from .redis import Redis
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = getenv("JWT_SECRET_KEY", "")


def check_secret_key():
    if SECRET_KEY == "":
        raise Exception("You have to set a Secret Key for JWT Auth")


check_secret_key()

ALGORITHM = getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(getenv("JWT_REFRESH_TOKEN_EXPIRE_MINUTES", f"{60 * 6}"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

bearer_scheme = HTTPBearer()


async def get_token(token=Depends(bearer_scheme)) -> str:
    """Fastapi Dependency to get the JWT/Bearer Token"""
    return str(token.credentials)


async def create_jwt_token(data: dict, expires_delta: timedelta) -> str:
    """Creates an JWT Token with `data` and `expire_delta`"""
    data = data.copy()
    expire = datetime.utcnow() + expires_delta
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_data(token: str = Depends(get_token)) -> Dict:
    """Fastapi Dependency to get JWT Data from the User"""
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.exceptions.InvalidTokenError as e:
        if isinstance(e, jwt.exceptions.ExpiredSignatureError):
            raise HTTPException(status_code=401, detail="Token is expired")
        raise HTTPException(status_code=401, detail="Token is invalid")
    return data


async def create_access_token(data: Dict) -> str:
    """Creates an JWT Access Token with `data` and expires after `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`"""
    return await create_jwt_token(data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


async def create_refresh_token(user_id: int, redis: Redis) -> str:
    """Creates an Refresh Token with the `user_id` and needs `redis`"""
    refresh_token_data: Dict = {"user_id": user_id}
    refresh_token: str = await create_jwt_token(refresh_token_data, timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
    await redis.sadd("refresh_tokens", refresh_token)
    return refresh_token


async def invalidate_refresh_token(refresh_token: str, redis: Redis) -> None:
    """Invalidates a Refresh Token"""
    await redis.srem("refresh_tokens", refresh_token)


async def check_refresh_token(refresh_token: str, redis: Redis) -> bool:
    """Checks if a Refresh Token is valid (in Redis Cache)"""
    refresh_tokens = [refresh_token.decode("utf-8") for refresh_token in await redis.smembers("refresh_tokens")]
    if refresh_token in refresh_tokens:
        return True
    return False


async def generate_tokens(data: Dict, user_id: int, redis: Redis) -> Dict:
    """Generates Access and Refresh Token with `data`, `user_id` and needs redis"""
    access_token: str = await create_access_token(data)
    refresh_token: str = await create_refresh_token(int(user_id), redis)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
