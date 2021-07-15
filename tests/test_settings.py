from unittest import IsolatedAsyncioTestCase

from fastapi_framework import redis_dependency, Redis
from fastapi_framework.settings import SettingsModel, Settings
from fastapi_framework.database import database_dependency, DB, select


class TestSettings(IsolatedAsyncioTestCase):
    async def test_settings_set(self):
        db: DB = await database_dependency()
        redis: Redis = await redis_dependency()

        await Settings.set("test_settings_set", "test")

        self.assertEqual((await db.first(select(SettingsModel).filter_by(key="test_settings_set"))).value, "test")
        self.assertEqual(await redis.get("settings:test_settings_set"), b"test")

    async def test_settings_get(self):
        await Settings.set("test_settings_get", "test_value")

        result = await Settings.get("test_settings_get")

        self.assertEqual(result, "test_value")

    async def test_settings_set_with_bool(self):
        db: DB = await database_dependency()
        redis: Redis = await redis_dependency()

        await Settings.set("test_settings_set_with_bool", True)
        await Settings.set("test_settings_set_with_bool_false", False)

        self.assertEqual(
            (await db.first(select(SettingsModel).filter_by(key="test_settings_set_with_bool"))).value, "1"
        )
        self.assertEqual(await redis.get("settings:test_settings_set_with_bool"), b"1")
        self.assertEqual(
            (await db.first(select(SettingsModel).filter_by(key="test_settings_set_with_bool_false"))).value, "0"
        )
        self.assertEqual(await redis.get("settings:test_settings_set_with_bool_false"), b"0")

    async def test_settings_change_value(self):
        await Settings.set("test_settings_change_value", "old_value")
        await Settings.set("test_settings_change_value", "test_value")

        self.assertEqual(await Settings.get("test_settings_change_value"), "test_value")

    async def test_settings_get_uncached_value(self):
        redis: Redis = await redis_dependency()

        await Settings.set("test_settings_get_uncached_value", "test_value")
        await redis.delete("settings:test_settings_get_uncached_value")
        result = await Settings.get("test_settings_get_uncached_value")

        self.assertEqual(result, "test_value")

    async def test_settings_get_not_exists(self):
        result = await Settings.get("test_settings_get_not_exists")

        self.assertEqual(result, None)
