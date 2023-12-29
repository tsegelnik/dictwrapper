from typing import Sequence, Tuple, Union
from orderedset import OrderedSet

TupleKey = Tuple[str, ...]
Key = Union[str, Tuple[str, ...]]
KeyLike = Union[str, Sequence[str]]


def properkey(key: KeyLike, sep: str | bool | None = None) -> Tuple[str, ...]:
    if isinstance(key, str):
        if isinstance(sep, str):
            return tuple(key.split(sep))
        elif sep==True:
            return tuple(key.split("."))

        return (key,)
    if isinstance(key, Tuple):
        return key

    return tuple(key)


def setkey(key: KeyLike) -> OrderedSet[str]:
    if isinstance(key, str):
        return OrderedSet((key,))

    return OrderedSet(key)
