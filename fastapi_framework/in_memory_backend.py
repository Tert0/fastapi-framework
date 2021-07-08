import time
from typing import Dict, Any, Optional, Set
from abc import ABC


class InMemoryBackend(ABC):
    async def set(self, key: str, value, expire: int = 0, pexpire: int = 0, exists=None):
        """Set Key to Value"""

    async def get(self, key: str):
        """Get Value from Key"""

    async def pttl(self, key: str) -> int:
        """Get PTTL from a Key"""

    async def ttl(self, key: str) -> int:
        """Get TTL from a Key"""

    async def pexpire(self, key: str, pexpire: int) -> bool:
        """Sets and PTTL for a Key"""

    async def expire(self, key: str, expire: int) -> bool:
        """Sets and TTL for a Key"""

    async def incr(self, key: str) -> int:
        """Increases an Int Key"""

    async def decr(self, key: str) -> int:
        """Decreases an Int Key"""

    async def delete(self, key: str):
        """Delete value of a Key"""

    async def smembers(self, key: str) -> Set:
        """Gets Set Members"""

    async def sadd(self, key: str, value: Any) -> bool:
        """Adds a Member to a Dict"""

    async def srem(self, key: str, member: Any) -> bool:
        """Removes a Member from a Set"""


class RAMBackendItem:
    value: Any
    pexpire: int
    timestamp: int

    def __init__(self, value: Any, pexpire: int):
        self.value = value
        self.pexpire = pexpire
        self.timestamp = int(time.time() * 1000)


class RAMBackend(InMemoryBackend):
    data: Dict[str, RAMBackendItem] = {}
    SET_IF_NOT_EXIST = "SET_IF_NOT_EXIST"  # NX
    SET_IF_EXIST = "SET_IF_EXIST"  # XX

    async def _check_key_expire(self, key: str, item: RAMBackendItem):
        timestamp = int(time.time() * 1000)
        if item.pexpire > 0 and (item.timestamp + item.pexpire) <= timestamp:
            self.data.pop(key)
            return False
        return True

    async def set(self, key: str, value, expire: int = 0, pexpire: int = 0, exists=None):
        if exists == self.SET_IF_NOT_EXIST:
            if key in self.data:
                return
        elif exists == self.SET_IF_EXIST:
            if key not in self.data:
                return
        elif exists is None:
            pass
        else:
            raise Exception("Wrong Params")
        self.data[key] = RAMBackendItem(value, pexpire + (expire * 1000))

    async def get(self, key: str):
        item: Optional[RAMBackendItem] = self.data.get(key)
        if not item:
            return None
        if not await self._check_key_expire(key, item):
            return None
        return item.value

    async def pttl(self, key: str) -> int:
        item: Optional[RAMBackendItem] = self.data.get(key)
        timestamp = int(time.time() * 1000)
        if not item:
            return -2
        if not await self._check_key_expire(key, item):
            return -1
        if item.pexpire == 0:
            return -1
        return (item.pexpire + item.timestamp) - timestamp

    async def ttl(self, key: str) -> int:
        pttl = await self.pttl(key)
        if pttl >= 0:
            return pttl // 1000
        return pttl

    async def pexpire(self, key: str, pexpire: int) -> bool:
        item: Optional[RAMBackendItem] = self.data.get(key)
        timestamp = int(time.time() * 1000)
        if not item:
            return False
        if not await self._check_key_expire(key, item):
            return False
        item.timestamp = timestamp
        item.pexpire = pexpire
        self.data[key] = item
        return True

    async def expire(self, key: str, expire: int) -> bool:
        return await self.pexpire(key, expire * 1000)

    async def incr(self, key: str) -> int:
        item: Optional[RAMBackendItem] = self.data.get(key)
        if not item:
            await self.set(key, 1)
            return 1
        if not isinstance(item.value, int):
            raise Exception("Value must be a Int")
        item.value += 1
        self.data[key] = item
        return item.value

    async def decr(self, key: str) -> int:
        item: Optional[RAMBackendItem] = self.data.get(key)
        if not item:
            await self.set(key, -1)
            return -1
        if not isinstance(item.value, int):
            raise Exception("Value must be a Int")
        item.value -= 1
        self.data[key] = item
        return item.value

    async def delete(self, key: str):
        if key not in self.data:
            return
        del self.data[key]

    async def smembers(self, key: str) -> Set:
        return await self.get(key)

    async def sadd(self, key: str, value: Any) -> bool:
        data: Optional[Set] = await self.get(key)
        if not data:
            data = {value}
        else:
            data.add(value)
        await self.set(key, data)
        return True

    async def srem(self, key: str, member: Any) -> bool:
        data: Optional[Set] = await self.get(key)
        if not data:
            return False
        if member not in data:
            return False
        data.remove(member)
        await self.set(key, data)
        return True
