from collections.abc import Sequence

from ordered_set import OrderedSet

TupleKey = tuple[str, ...]
Key = str | tuple[str, ...]
KeyLike = str | Sequence[str]


def properkey(key: KeyLike, *, sep: str | bool | None = None) -> TupleKey:
    if isinstance(key, str):
        if isinstance(sep, str):
            return tuple(key.split(sep))
        elif sep is True:
            return tuple(key.split("."))
        return (key,)
    return key if isinstance(key, tuple) else tuple(key)


def orderedsetkey(key: KeyLike) -> OrderedSet[str]:
    return OrderedSet((key,)) if isinstance(key, str) else OrderedSet(key)


def setkey(key: KeyLike) -> set[str]:
    return {key} if isinstance(key, str) else set(key)


def strkey(key: KeyLike, *, sep=".") -> str:
    return key if isinstance(key, str) else sep.join(key)
