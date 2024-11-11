"""
Utility functions used throughout this library and is not meant to be used by other packages.
"""

from typing import TypeVar

__all__ = [
    'deduplicate_list',
    'to_snake_case',
]


T = TypeVar('T')


def deduplicate_list(items: list[T]) -> list[T]:
    """Deduplicate a list."""

    if not len(items) > 1:
        return items

    return list(dict.fromkeys(items))


def to_snake_case(key: str) -> str:
    """Convert a key to snake_case."""

    return '_'.join(key.strip().split(' '))
