from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import StorageKey
from typing import Dict, Any

class CacheManager:
    def __init__(self, storage):
        self.storage = storage

    async def cache_data(self, key: StorageKey, data: Dict[str, Any]):
        await self.storage.set_data(key=key, data=data)

    async def get_cached_data(self, key: StorageKey) -> Dict[str, Any]:
        return await self.storage.get_data(key=key)