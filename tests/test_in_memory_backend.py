import asyncio
from typing import Set
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock

from fastapi_framework.in_memory_backend import RAMBackend

ram_backend = RAMBackend()


class TestInMemoryBackend(IsolatedAsyncioTestCase):
    async def test_init_ram_backend(self):
        RAMBackend()

    async def test_set_value(self):
        await ram_backend.set("test_set_value", "test_value")

        self.assertTrue("test_set_value" in ram_backend.data)
        self.assertEqual(ram_backend.data["test_set_value"].value, b"test_value")

    async def test_get_value(self):
        await ram_backend.set("test_get_value", "test_value")

        self.assertEqual(await ram_backend.get("test_get_value"), b"test_value")

    async def test_set_value_wrong_params(self):
        with self.assertRaises(Exception):
            await ram_backend.set("test_set_value_wrong_params", "test_value", exists="WRONG")

    async def test_set_value_with_pttl(self):
        await ram_backend.set("test_set_value_with_pttl", "test_value", pexpire=2000)

        self.assertTrue("test_set_value_with_pttl" in ram_backend.data)
        pexpire = ram_backend.data["test_set_value_with_pttl"].pexpire
        self.assertIsInstance(pexpire, int)
        self.assertTrue(pexpire <= 2000)

    async def test_set_value_with_ttl(self):
        await ram_backend.set("test_set_value_with_ttl", "test_value", expire=10)

        self.assertTrue("test_set_value_with_ttl" in ram_backend.data)
        expire = int(ram_backend.data["test_set_value_with_ttl"].pexpire / 1000)
        self.assertIsInstance(expire, int)
        self.assertTrue(expire <= 10)

    async def test_get_pttl(self):
        await ram_backend.set("test_get_pttl", "test_value", expire=10)

        self.assertTrue("test_get_pttl" in ram_backend.data)

        pexpire = ram_backend.data["test_get_pttl"].pexpire

        pexpire_getter = await ram_backend.pttl("test_get_pttl")

        self.assertIsInstance(pexpire, int)
        self.assertIsInstance(pexpire, int)
        self.assertTrue(pexpire_getter <= pexpire)

    async def test_get_pttl_key_dont_exists(self):
        self.assertEqual(await ram_backend.pttl("this_key_doesn't_exists"), -2)

    async def test_get_pttl_with_expired_key(self):
        await ram_backend.set("test_get_pttl_with_expired_key", "test_value", pexpire=1)
        await asyncio.sleep(0.01)

        self.assertEqual(await ram_backend.pttl("test_get_pttl_with_expired_key"), -1)

    async def test_get_value_not_existing(self):
        self.assertEqual(await ram_backend.get("this_key_doesn't_exists"), None)

    async def test_pexpire(self):
        await ram_backend.set("test_pexpire", "test_value")
        await ram_backend.pexpire("test_pexpire", 1000)

        self.assertTrue("test_pexpire" in ram_backend.data)
        self.assertEqual(ram_backend.data["test_pexpire"].pexpire, 1000)

    async def test_pexpire_dont_exsist(self):
        self.assertEqual(await ram_backend.pexpire("this_key_doesn't_exists", 1), False)

    @patch("fastapi_framework.in_memory_backend.RAMBackend.pexpire")
    async def test_expire(self, pexpire_patch: AsyncMock):
        await ram_backend.expire("test", 15)

        pexpire_patch.assert_called_with("test", 15000)

    async def test_increase(self):
        await ram_backend.set("test_increase", 1)

        for _ in range(10):
            await ram_backend.incr("test_increase")

        self.assertEqual(await ram_backend.get("test_increase"), b"11")

    async def test_decrease(self):
        await ram_backend.set("test_decrease", 11)

        for _ in range(10):
            await ram_backend.decr("test_decrease")

        self.assertEqual(await ram_backend.get("test_decrease"), b"1")

    async def test_increase_dont_exists(self):
        for _ in range(10):
            await ram_backend.incr("test_increase_dont_exists")

        self.assertEqual(await ram_backend.get("test_increase_dont_exists"), b"10")

    async def test_decrease_dont_exists(self):
        for _ in range(10):
            await ram_backend.decr("test_decrease_dont_exists")

        self.assertEqual(await ram_backend.get("test_decrease_dont_exists"), b"-10")

    async def test_increase_with_string(self):
        await ram_backend.set("test_increase_with_string", "hello")

        with self.assertRaises(Exception):
            await ram_backend.incr("test_increase_with_string")

    async def test_decrease_with_string(self):
        await ram_backend.set("test_decrease_with_string", "hello")

        with self.assertRaises(Exception):
            await ram_backend.decr("test_decrease_with_string")

    async def test_get_expired_key(self):
        await ram_backend.set("test_get_expired_key", "test_value", pexpire=1)

        await asyncio.sleep(0.001)

        self.assertEqual(await ram_backend.get("test_get_expired_key"), None)

    async def test_get_ttl(self):
        await ram_backend.set("test_get_ttl", "test_value", expire=10)

        self.assertIsInstance(await ram_backend.ttl("test_get_ttl"), int)
        self.assertTrue(await ram_backend.ttl("test_get_ttl") <= 10)

    async def test_get_ttl_not_expiring(self):
        await ram_backend.set("test_get_ttl_not_expiring", "test_value")

        result = await ram_backend.ttl("test_get_ttl_not_expiring")
        self.assertIsInstance(result, int)
        self.assertEqual(result, -1)

    async def test_pexpire_with_expired_key(self):
        await ram_backend.set("test_pexpire_with_expired_key", "test_value", pexpire=1)
        await asyncio.sleep(0.001)

        result = await ram_backend.pexpire("test_pexpire_with_expired_key", 1)
        self.assertIsInstance(result, bool)
        self.assertEqual(result, False)

    async def test_delete(self):
        await ram_backend.set("test_delete", "test_value")

        self.assertEqual(await ram_backend.get("test_delete"), b"test_value")

        await ram_backend.delete("test_delete")

        self.assertEqual(await ram_backend.get("test_delete"), None)

    async def test_delete_dont_exists(self):
        await ram_backend.delete("test_delete_dont_exists")

    async def test_set_if_not_exists_and_set_if_exists(self):
        await ram_backend.set("test_set_if_not_exists", "1", exists=ram_backend.SET_IF_NOT_EXIST)

        self.assertEqual(await ram_backend.get("test_set_if_not_exists"), b"1")

        await ram_backend.set("test_set_if_not_exists", "2", exists=ram_backend.SET_IF_NOT_EXIST)

        self.assertEqual(await ram_backend.get("test_set_if_not_exists"), b"1")

        await ram_backend.set("test_set_if_not_exists", "3", exists=ram_backend.SET_IF_EXIST)

        self.assertEqual(await ram_backend.get("test_set_if_not_exists"), b"3")

        del ram_backend.data["test_set_if_not_exists"]
        await ram_backend.set("test_set_if_not_exists", "4", exists=ram_backend.SET_IF_EXIST)

        self.assertEqual(await ram_backend.get("test_set_if_not_exists"), None)

    async def test_smembers_with_empty_set(self):
        result: Set = await ram_backend.smembers("test_smembers_with_empty_set")

        self.assertEqual(result, set())

    async def test_sadd_item_to_set(self):
        await ram_backend.sadd("test_sadd_item_to_set", "test_value_1")

        self.assertEqual(await ram_backend.smembers("test_sadd_item_to_set"), {"test_value_1"})

    async def test_sadd_multiple_values(self):
        for i in range(5):
            await ram_backend.sadd("test_sadd_multiple_values", f"test_value_{i}")

        self.assertEqual(
            await ram_backend.smembers("test_sadd_multiple_values"), set(map(lambda x: f"test_value_{x}", range(5)))
        )

    async def test_srem(self):
        await ram_backend.sadd("test_srem", "test_srem_1")
        await ram_backend.sadd("test_srem", "test_srem_2")

        self.assertEqual(await ram_backend.smembers("test_srem"), {"test_srem_1", "test_srem_2"})

        await ram_backend.srem("test_srem", "test_srem_2")

        self.assertEqual(await ram_backend.smembers("test_srem"), {"test_srem_1"})

    async def test_srem_member_dont_exists(self):
        await ram_backend.sadd("test_srem_member_dont_exists", "test_srem_1")

        self.assertEqual(await ram_backend.srem("test_srem_member_dont_exists", "test"), False)

    async def test_srem_key_dont_exists(self):
        self.assertEqual(await ram_backend.srem("test_srem_key_dont_exists", "test"), False)

    async def test_exists(self):
        self.assertEqual(await ram_backend.exists("test_exists"), False)

        await ram_backend.set("test_exists", "test_value")

        self.assertEqual(await ram_backend.exists("test_exists"), True)

    async def test_smembers_with_string(self):
        await ram_backend.set("test_smembers_with_string", "test_value")

        self.assertEqual(await ram_backend.smembers("test_smembers_with_string"), {b"test_value"})

    async def test_increase_with_list(self):
        await ram_backend.set("test_increase_with_list", ["test"])

        with self.assertRaises(Exception):
            await ram_backend.incr("test_increase_with_list")

    async def test_decrease_with_list(self):
        await ram_backend.set("test_decrease_with_list", ["test"])

        with self.assertRaises(Exception):
            await ram_backend.decr("test_decrease_with_list")
