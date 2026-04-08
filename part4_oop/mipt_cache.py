from dataclasses import dataclass
from typing import TypeVar

from part4_oop.interfaces import Policy, Storage

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class MIPTCache[K, V]:
    storage: Storage[K, V]
    policy: Policy[K]

    def set(self, key: K, value: V) -> None:
        self._store_key(key, value)
        key_to_evict = self.policy.get_key_to_evict()
        if key_to_evict is not None:
            self.remove(key_to_evict)

    def get(self, key: K) -> V | None:
        if not self.exists(key):
            return None

        self.policy.register_access(key)
        return self.storage.get(key)

    def exists(self, key: K) -> bool:
        return self.storage.exists(key)

    def remove(self, key: K) -> None:
        self.storage.remove(key)
        self.policy.remove_key(key)

    def clear(self) -> None:
        self.storage.clear()
        self.policy.clear()

    def _store_key(self, key: K, value: V) -> None:
        self.storage.set(key, value)
        self.policy.register_access(key)
