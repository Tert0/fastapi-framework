import time
from typing import Dict, Any, Optional, Set, Union, List
from abc import ABC, abstractmethod


class InMemoryBackend(ABC):
    @abstractmethod
    async def set(self, key: str, value, expire: int = 0, pexpire: int = 0, exists=None):
        """Set Key to Value"""

    @abstractmethod
    async def get(self, key: str):
        """Get Value from Key"""

    @abstractmethod
    async def pttl(self, key: str) -> int:
        """Get PTTL from a Key"""

    @abstractmethod
    async def ttl(self, key: str) -> int:
        """Get TTL from a Key"""

    @abstractmethod
    async def pexpire(self, key: str, pexpire: int) -> bool:
        """Sets and PTTL for a Key"""

    @abstractmethod
    async def expire(self, key: str, expire: int) -> bool:
        """Sets and TTL for a Key"""

    @abstractmethod
    async def incr(self, key: str) -> int:
        """Increases an Int Key"""

    @abstractmethod
    async def decr(self, key: str) -> int:
        """Decreases an Int Key"""

    @abstractmethod
    async def delete(self, key: str):
        """Delete value of a Key"""

    @abstractmethod
    async def smembers(self, key: str) -> Set:
        """Gets Set Members"""

    @abstractmethod
    async def sadd(self, key: str, value: Any) -> bool:
        """Adds a Member to a Set"""

    @abstractmethod
    async def srem(self, key: str, member: Any) -> bool:
        """Removes a Member from a Set"""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Checks if a Key exists"""


class RAMBackendItem:
    """Key-Value Item for the RAM Backend"""

    value: Union[bytes, List]
    pexpire: int
    timestamp: int

    def __init__(self, value: Any, pexpire: int):
        self.value = value
        self.pexpire = pexpire
        self.timestamp = int(time.time() * 1000)


class RAMBackend(InMemoryBackend):
    """Python In Memory Backend"""

    data: Dict[str, RAMBackendItem] = {}
    SET_IF_NOT_EXIST = "SET_IF_NOT_EXIST"  # NX
    SET_IF_EXIST = "SET_IF_EXIST"  # XX

    async def _check_key_expire(self, key: str, item: RAMBackendItem):
        """Checks if a Key is expired and deletes it"""
        timestamp = int(time.time() * 1000)
        if item.pexpire > 0 and (item.timestamp + item.pexpire) <= timestamp:
            self.data.pop(key)
            return False
        return True

    async def set(self, key: str, value: Any, expire: int = 0, pexpire: int = 0, exists=None):
        """Set Key to Value"""
        if not isinstance(value, bytes) and not isinstance(value, List):
            value = bytes(str(value), "utf-8")
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
        """Get Value from Key"""
        item: Optional[RAMBackendItem] = self.data.get(key)
        if not item:
            return None
        if not await self._check_key_expire(key, item):
            return None
        return item.value

    async def pttl(self, key: str) -> int:
        """Get PTTL from a Key"""
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
        """Get TTL from a Key"""
        pttl = await self.pttl(key)
        if pttl >= 0:
            return pttl // 1000
        return pttl

    async def pexpire(self, key: str, pexpire: int) -> bool:
        """Sets and PTTL for a Key"""
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
        """Sets and TTL for a Key"""
        return await self.pexpire(key, expire * 1000)

    async def incr(self, key: str) -> int:
        """Increases an Int Key"""
        item: Optional[RAMBackendItem] = self.data.get(key)
        if not item:
            await self.set(key, 1)
            return 1
        try:
            if not isinstance(item.value, bytes):
                raise Exception("Value must be a Int")
            item.value = bytes(str(int(item.value.decode("utf-8")) + 1), "utf-8")
        except ValueError:
            raise Exception("Value must be a Int")
        self.data[key] = item
        return int(item.value.decode("utf-8"))

    async def decr(self, key: str) -> int:
        """Decreases an Int Key"""
        item: Optional[RAMBackendItem] = self.data.get(key)
        if not item:
            await self.set(key, -1)
            return -1
        try:
            if not isinstance(item.value, bytes):
                raise Exception("Value must be a Int")
            item.value = bytes(str(int(item.value.decode("utf-8")) - 1), "utf-8")
        except ValueError:
            raise Exception("Value must be a Int")
        self.data[key] = item
        return int(item.value.decode("utf-8"))

    async def delete(self, key: str):
        """Delete value of a Key"""
        if key not in self.data:
            return
        del self.data[key]

    async def smembers(self, key: str) -> Set:
        """Gets Set Members"""
        data: Optional[Union[bytes, List]] = await self.get(key)
        if not data:
            return set()
        if not isinstance(data, list):
            return {data}
        return set(data)

    async def sadd(self, key: str, value: Any) -> bool:
        """Adds a Member to a Set"""
        data: Union[Optional[Union[bytes, List]], Set] = await self.get(key)
        if not data or not isinstance(data, List):
            data = {value}
        else:
            data = set(data)
            data.add(value)
        await self.set(key, list(data))
        return True

    async def srem(self, key: str, member: Any) -> bool:
        """Removes a Member from a Set"""
        data: Union[Optional[Union[bytes, List]], Set] = await self.get(key)
        if not data or not isinstance(data, List):
            return False
        data = set(data)
        if member not in data:
            return False
        data.remove(member)
        await self.set(key, list(data))
        return True

    async def exists(self, key: str) -> bool:
        """Checks if a Key exists"""
        return key in self.data
