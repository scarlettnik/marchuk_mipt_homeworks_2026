from dataclasses import dataclass, field
from typing import TypeVar

from part4_oop.interfaces import Policy

K = TypeVar("K")


def register_new_key[K](order: list[K], key: K) -> None:
    if key in order:
        return
    order.append(key)


def move_key_to_end[K](order: list[K], key: K) -> None:
    if key in order:
        order.remove(key)
    order.append(key)


def get_first_key_to_evict[K](order: list[K], capacity: int) -> K | None:
    if len(order) <= capacity:
        return None
    return order[0]


def remove_key_from_order[K](order: list[K], key: K) -> None:
    if key in order:
        order.remove(key)


def get_last_registered_key[K](key_counter: dict[K, int]) -> K | None:
    last_registered_key: K | None = None
    for key in key_counter:
        last_registered_key = key
    return last_registered_key


def get_least_used_key[K](
    key_counter: dict[K, int],
    last_registered_key: K | None,
    capacity: int,
) -> K | None:
    least_used_key: K | None = None
    least_count = 0
    for key, count in key_counter.items():
        if capacity != 0 and key == last_registered_key:
            continue
        if least_used_key is None or count < least_count:
            least_used_key = key
            least_count = count
    return least_used_key


@dataclass
class FIFOPolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)

    def register_access(self, key: K) -> None:
        register_new_key(self._order, key)

    def get_key_to_evict(self) -> K | None:
        return get_first_key_to_evict(self._order, self.capacity)

    def remove_key(self, key: K) -> None:
        remove_key_from_order(self._order, key)

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
        move_key_to_end(self._order, key)

    def get_key_to_evict(self) -> K | None:
        return get_first_key_to_evict(self._order, self.capacity)

    def remove_key(self, key: K) -> None:
        remove_key_from_order(self._order, key)

    def clear(self) -> None:
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return bool(self._order)


@dataclass
class LFUPolicy(Policy[K]):
    capacity: int = 5
    _key_counter: dict[K, int] = field(default_factory=dict, init=False)

    def register_access(self, key: K) -> None:
        count = self._key_counter.get(key)
        if count is not None:
            self._key_counter[key] = count + 1
            return
        self._key_counter[key] = 1

    def get_key_to_evict(self) -> K | None:
        if len(self._key_counter) <= self.capacity:
            return None

        last_registered_key = get_last_registered_key(self._key_counter)
        return get_least_used_key(self._key_counter, last_registered_key, self.capacity)

    def remove_key(self, key: K) -> None:
        self._key_counter.pop(key, None)

    def clear(self) -> None:
        self._key_counter.clear()

    @property
    def has_keys(self) -> bool:
        return bool(self._key_counter)
