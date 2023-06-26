"""A FastAPI Framework for things like Database, Redis, Logging, JWT Authentication and Rate Limits"""

__version__ = "1.5.3.4"

from .modules import check_dependencies, disabled_modules

check_dependencies()  # noqa: FLK-E402
from .database import database_dependency
from .jwt_auth import (
    create_jwt_token,
    create_access_token,
    create_refresh_token,
    invalidate_refresh_token,
    get_token,
    get_data,
    pwd_context,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    check_refresh_token,
    generate_tokens,
)
from .logger import get_logger
from .rate_limit import RateLimitManager, RateLimiter, get_uuid_user_id, RateLimitTime
from .redis import get_redis, RedisDependency, redis_dependency, Redis
from .in_memory_backend import InMemoryBackend, RAMBackend
from .config import Config, ConfigField
from .session import Session
