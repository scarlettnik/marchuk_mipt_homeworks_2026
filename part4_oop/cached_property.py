from collections.abc import Callable
from typing import Any, TypeVar

from part4_oop.interfaces import HasCache

V = TypeVar("V")


class CachedProperty[V]:
    _cache_key: str

    def __init__(self, func: Callable[..., V]) -> None:
        self._getter = func

    def __set_name__(self, _owner: type[Any], name: str) -> None:
        self._cache_key = name

    def __get__(self, instance: HasCache[str, V] | None, _owner: type[Any]) -> Any:
        if instance is None:
            return self

        if instance.cache.exists(self._cache_key):
            return instance.cache.get(self._cache_key)

        return self._calculate_value(instance)

    def _calculate_value(self, instance: HasCache[str, V]) -> V:
        value = self._getter(instance)
        instance.cache.set(self._cache_key, value)
        return value
