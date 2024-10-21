from __future__ import annotations

from typing import TYPE_CHECKING

from ..nestedmkdict import NestedMKDict
from ..typing import setkey

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from typing import Any

    from ..typing import Key, KeyLike


def mkmap(
    fcn: Callable,
    arg0: NestedMKDict,
    *args: NestedMKDict,
    sep: int | str | bool | None = None,
) -> NestedMKDict:
    match sep:
        case False:
            # False matches case 0, but 0 does not match case False
            sep = None
        case 0 | True:
            sep = arg0._sep
        case int():
            if sep > 0:
                sep = args[sep - 1]._sep
            elif sep >= -len(args):
                sep = args[sep]._sep
            else:
                raise IndexError()
        case str() | None:
            pass
        case _:
            raise TypeError(f"Invalid sep: {sep}")
    ret = NestedMKDict({}, sep=sep)
    for key, value0 in arg0.walkitems():
        values = (arg[key] for arg in args)
        ret[key] = fcn(value0, *values)
    return ret


def remap_items(
    source: NestedMKDict,
    target: NestedMKDict | None = None,
    *,
    rename_indices: Mapping[str, Sequence[str]] | None = None,
    reorder_indices: (
        tuple[int]
        | tuple[tuple[str, ...], tuple[str, ...]]
        | list[int]
        | list[list[str]]
        | None
    ) = None,
    skip_indices_source: Sequence[KeyLike | set] | None = None,
    skip_indices_target: Sequence[KeyLike | set] | None = None,
    fcn: Callable[[Any], Any] = lambda o: o,
) -> NestedMKDict:
    from itertools import product

    if target is None:
        target = NestedMKDict()

    skip_source = _make_skip_fcn(skip_indices_source)
    skip_target = _make_skip_fcn(skip_indices_target)
    reorder = _make_reorder_fcn(reorder_indices)

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


def _make_skip_fcn(
    skip_indices: Sequence[KeyLike | set] | None,
) -> Callable[[Key], bool]:
    if skip_indices is not None:
        skip_sets: tuple[set[str], ...] = tuple(
            sq if isinstance(sq, set) else setkey(sq) for sq in skip_indices
        )
        return lambda key: any(ss.issubset(key) for ss in skip_sets)

    return lambda _: False


def _make_reorder_fcn(
    reorder_indices: (
        tuple[int]
        | tuple[tuple[str, ...], tuple[str, ...]]
        | list[int]
        | list[list[str]]
        | None
    )
) -> Callable[[Key], Key]:
    match reorder_indices:
        case [int(), *_]:
            index_order = reorder_indices
        case [[str(), *_], [str(), *_]]:
            order_from, order_to = reorder_indices
            if len(order_from) != len(order_to) or set(order_from) != set(order_to):
                raise ValueError(
                    f"Inconsistent order definitions: {order_from} and {order_to}"
                )
            try:
                index_order = tuple(order_from.index(item) for item in order_to)
            except ValueError:
                raise ValueError(
                    f"Inconsistent order definitions {order_from} and {order_to}"
                )
        case None:
            return lambda key: key
        case _:
            raise ValueError(f"Invalid order specification: {reorder_indices}")

    return lambda key: tuple(key[idx] for idx in index_order)
