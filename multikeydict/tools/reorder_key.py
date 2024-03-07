from collections.abc import Sequence

from ..typing import TupleKey


def reorder_key(key: TupleKey, key_order: Sequence[int] | None = None):
    if key_order is None:
        return key
    return tuple(key[i] for i in key_order)
