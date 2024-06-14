from __future__ import annotations

from typing import TYPE_CHECKING

from ..nestedmkdict import NestedMKDict
from ..typing import setkey

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from typing import Any

    from ..typing import Key, KeyLike


def remap_items(
    source: NestedMKDict,
    target: NestedMKDict | None = None,
    *,
    rename_indices: Mapping[str, Sequence[str]] | None = None,
    reorder_indices: (
        tuple[int] | tuple[tuple[str,...], tuple[str,...]] | list[int] | list[list[str]] | None
    ) = None,
    skip_indices_source: Sequence[KeyLike | set] | None = None,
    skip_indices_target: Sequence[KeyLike | set] | None = None,
    fcn: Callable[[Any], Any] = lambda o: o,
) -> NestedMKDict:
    from itertools import product

    if target is None:
        target = NestedMKDict()

    skip_source = make_skip_fcn(skip_indices_source)
    skip_target = make_skip_fcn(skip_indices_target)
    reorder = make_reorder_fcn(reorder_indices)

    if rename_indices is not None:
        for key, value in source.walkitems():
            if skip_source(key):
                continue
            for newkey in product(
                *tuple(rename_indices.get(skey, (skey,)) for skey in key)
            ):
                newkey_ordered = reorder(newkey)
                if skip_target(newkey_ordered):
                    continue
                target[newkey_ordered] = fcn(value)
    else:
        for key, value in source.walkitems():
            newkey_ordered = reorder(key)
            if skip_target(newkey_ordered):
                continue
            target[newkey_ordered] = fcn(value)

    return target


def make_skip_fcn(skip_indices: Sequence[KeyLike | set] | None) -> Callable[[Key], bool]:
    if skip_indices is not None:
        skip_sets: tuple[set[str], ...] = tuple(
            sq if isinstance(sq, set) else setkey(sq) for sq in skip_indices
        )
        return lambda key: any(ss.issubset(key) for ss in skip_sets)

    return lambda _: False


def make_reorder_fcn(
    reorder_indices: (
        tuple[int] | tuple[tuple[str,...], tuple[str,...]] | list[int] | list[list[str]] | None
    )
) -> Callable[[Key], Key]:
    match reorder_indices:
        case [int(), *_]:
            index_order = reorder_indices
        case [[str(), *_], [str(), *_]]:
            order1, order2 = reorder_indices
            if len(order1) != len(order2) or set(order1) != set(order2):
                raise ValueError(f"Order definitions are inconsistent: {order1} and {order2}")
            index_order = tuple(order1.index(item) for item in order2)
        case _:
            index_order = None
            return lambda key: key

    return lambda key: tuple(key[idx] for idx in index_order)
