from collections.abc import Sequence

from orderedset import OrderedSet

TupleKey = tuple[str, ...]
Key = str | tuple[str, ...]
KeyLike = str | Sequence[str]


def properkey(key: KeyLike, sep: str | bool | None = None) -> tuple[str, ...]:
    if isinstance(key, str):
        if isinstance(sep, str):
            return tuple(key.split(sep))
        elif sep is True:
            return tuple(key.split("."))

        return (key,)
    if isinstance(key, tuple):
        return key

    return tuple(key)


def orderedsetkey(key: KeyLike) -> OrderedSet[str]:
    if isinstance(key, str):
        return OrderedSet((key,))

    return OrderedSet(key)


def setkey(key: KeyLike) -> set[str]:
    if isinstance(key, str):
        return set((key,))

    return set(key)


def strkey(key: KeyLike, sep=".") -> str:
    if isinstance(key, str):
        return key

    return sep.join(key)
