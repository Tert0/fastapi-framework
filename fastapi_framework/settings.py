from os import getenv
from typing import Union, Optional

from sqlalchemy import Column, String

from .redis import redis_dependency, Redis
from .database import database_dependency, DB, select, Base

CACHE_TTL = int(getenv("CACHE_TTL", str(60 * 60 * 5)))


class SettingsModel(Base):
    __tablename__ = "settings"
    key: Union[str, Column] = Column(String(255), primary_key=True, unique=True)
    value: Union[str, Column] = Column(String())

    @staticmethod
    async def create(key: str, value: Union[str, int, float, bool], db: DB) -> "SettingsModel":
        row = SettingsModel(key=key, value=str(value))
        await db.add(row)
        return row


class Settings:
    """Project Settings"""

    @staticmethod
    async def set(key: str, value: Union[str, int, float, bool]):
        """Sets a Key to a Value and caches it"""
        redis: Redis = await redis_dependency()
        db: DB = await database_dependency()
        setting: SettingsModel
        if isinstance(value, bool):
            value = int(value)
        if (setting := await db.first(select(SettingsModel).filter_by(key=key))) is None:
            await SettingsModel.create(key, value, db)
        else:
            setting.value = value
        await db.commit()
        await redis.set(f"settings:{key}", value, expire=CACHE_TTL)

    @staticmethod
    async def get(key: str) -> Optional[str]:
        """Gets a Value from a Key"""
        redis: Redis = await redis_dependency()
        redis_key = f"settings:{key}"
        value: bytes
        if (value := await redis.get(redis_key)) is not None:
            return value.decode("utf-8")
        db: DB = await database_dependency()
        setting: SettingsModel = await db.first(select(SettingsModel).filter_by(key=key))
        if setting is None:
            return None
        await redis.set(redis_key, setting.value)
        return setting.value
