from dataclasses import dataclass, field
from typing import TypeVar

from part4_oop.interfaces import Policy

K = TypeVar("K")


@dataclass
class FIFOPolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)

    def register_access(self, key: K) -> None:
        if key in self._order:
            return
        self._order.append(key)

    def get_key_to_evict(self) -> K | None:
        if len(self._order) <= self.capacity:
            return None
        return self._order[0]

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return bool(self._order)


@dataclass
class LRUPolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)

    def register_access(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)
        self._order.append(key)

    def get_key_to_evict(self) -> K | None:
        if len(self._order) <= self.capacity:
            return None
        return self._order[0]

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return bool(self._order)


@dataclass
class LFUPolicy(Policy[K]):
    capacity: int = 5
    _key_counter: dict[K, int] = field(default_factory=dict, init=False)
    _last_registered_key: K | None = field(default=None, init=False)

    def register_access(self, key: K) -> None:
        count = self._key_counter.get(key)
        self._last_registered_key = key
        if count is not None:
            self._key_counter[key] = count + 1
            return
        self._key_counter[key] = 1

    def get_key_to_evict(self) -> K | None:
        if len(self._key_counter) <= self.capacity:
            return None

        return self._get_least_used_key()

    def remove_key(self, key: K) -> None:
        self._key_counter.pop(key, None)
        if key == self._last_registered_key:
            self._last_registered_key = None

    def clear(self) -> None:
        self._key_counter.clear()
        self._last_registered_key = None

    @property
    def has_keys(self) -> bool:
        return bool(self._key_counter)

    def _get_least_used_key(self) -> K | None:
        least_used_key: K | None = None
        least_count = 0
        for key, count in self._key_counter.items():
            if key == self._last_registered_key:
                continue
            if least_used_key is None or count < least_count:
                least_used_key = key
                least_count = count
        return least_used_key
