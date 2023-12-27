from typing import Sequence, Tuple, Union
from orderedset import OrderedSet

TupleKey = Tuple[str, ...]
Key = Union[str, Tuple[str, ...]]
KeyLike = Union[str, Sequence[str]]


def properkey(key: KeyLike) -> Tuple[str, ...]:
    if isinstance(key, str):
        return (key,)
    if isinstance(key, Tuple):
        return key

    return tuple(key)


def setkey(key: KeyLike) -> OrderedSet[str]:
    if isinstance(key, str):
        return OrderedSet((key,))

    return OrderedSet(key)
