from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def flatten(iterable: Iterable[T]) -> Iterable[T]:
    for item in iterable:
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            yield from flatten(item)
        else:
            yield item


def flatten_with_parent(iterable: Iterable[T]) -> T | Iterable[T]:
    for item in iterable:
        yield item
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            yield from flatten(item)
