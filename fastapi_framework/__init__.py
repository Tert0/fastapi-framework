"""A FastAPI Framework for things like Database, Redis, Logging, JWT Authentication and Rate Limits"""

__version__ = "1.5.4"

from .modules import check_dependencies, disabled_modules

check_dependencies()  # noqa: FLK-E402
from .config import Config, ConfigField
from .database import database_dependency
from .in_memory_backend import InMemoryBackend, RAMBackend
from .jwt_auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    check_refresh_token,
    create_access_token,
    create_jwt_token,
    create_refresh_token,
    generate_tokens,
    get_data,
    get_token,
    invalidate_refresh_token,
    pwd_context,
)
from .logger import get_logger
from .rate_limit import RateLimiter, RateLimitManager, RateLimitTime, get_uuid_user_id
from .redis import Redis, RedisDependency, get_redis, redis_dependency
from .session import Session
