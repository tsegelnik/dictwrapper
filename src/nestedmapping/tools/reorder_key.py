from collections.abc import Sequence

from ..typing import TupleKey


def reorder_key(key: TupleKey, key_order: Sequence[int] | None = None):
    return key if key_order is None else tuple(key[i] for i in key_order)
