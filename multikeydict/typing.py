from typing import Tuple, Sequence, Union

TupleKey = Tuple[str,...]
Key = Union[str, Tuple[str,...]]
KeyLike = Union[str, Sequence[str]]

def properkey(key: KeyLike) -> Tuple[str,...]:
    if isinstance(key, str):
        return key,

    return key
