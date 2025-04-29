from __future__ import annotations

from typing import TYPE_CHECKING

from ..nested_mapping import NestedMapping
from ..typing import setkey

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from typing import Any

    from ..typing import Key, KeyLike


def mkmap(
    fcn: Callable,
    arg0: NestedMapping,
    *args: NestedMapping,
    sep: int | str | bool | None = None,
) -> NestedMapping:
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
    ret = NestedMapping({}, sep=sep)
    for key, value0 in arg0.walkitems():
        values = (arg[key] for arg in args)
        ret[key] = fcn(value0, *values)
    return ret


def remap_items(
    source: NestedMapping,
    target: NestedMapping | None = None,
    *,
    rename_indices: Mapping[str, Sequence[str]] | None = None,
    reorder_indices: (
        tuple[int]
        | tuple[tuple[str, ...], tuple[str, ...]]
        | list[int]
        | list[list[str]]
        | Mapping[str, list[str] | tuple[str]]
        | None
    ) = None,
    skip_indices_source: Sequence[KeyLike | set] | None = None,
    skip_indices_target: Sequence[KeyLike | set] | None = None,
    fcn: Callable[[Any], Any] | None = None,
    verbose: bool = False,
) -> NestedMapping:
    from itertools import product

    if target is None:
        target = NestedMapping()

    skip_source = _make_skip_fcn(skip_indices_source)
    skip_target = _make_skip_fcn(skip_indices_target)
    reorder = make_reorder_function(reorder_indices)

    if fcn is None:
        fcn = lambda o: o
        has_fcn = False
    else:
        has_fcn = True

    if rename_indices is not None:
        for key, value in source.walkitems():
            if skip_source(key):
                continue
            for newkey in product(*tuple(rename_indices.get(skey, (skey,)) for skey in key)):
                newkey_ordered = reorder(newkey)
                if skip_target(newkey_ordered):
                    if verbose:
                        print(f"remap: skip {'.'.join(key)} → {'.'.join(newkey_ordered)}")
                    continue
                if verbose:
                    print(
                        f"remap {'(fcn) ' if has_fcn else ''}{'.'.join(key)} → {'.'.join(newkey_ordered)}"
                    )
                target[newkey_ordered] = fcn(value)
    else:
        for key, value in source.walkitems():
            newkey_ordered = reorder(key)
            if skip_target(newkey_ordered):
                if verbose:
                    print(f"remap: skip {'.'.join(key)} → {'.'.join(newkey_ordered)}")
                continue
            if verbose:
                print(
                    f"remap {'(fcn) ' if has_fcn else ''}{'.'.join(key)} → {'.'.join(newkey_ordered)}"
                )
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


def make_reorder_function(
    reorder_indices: (
        tuple[int]
        | tuple[tuple[str, ...], tuple[str, ...]]
        | Sequence[int]
        | Sequence[Sequence[str]]
        | Mapping[str, list[str] | tuple[str]]
        | None
    ),
    *,
    allow_skip_items: bool = False,
) -> Callable:
    match reorder_indices:
        case [int(), *_]:
            index_order = reorder_indices
            len_from = len(index_order)
        case [[str(), *_] as order_from, [str(), *_] as order_to] | {
            "from": [str(), *_] as order_from,
            "to": [str(), *_] as order_to,
        }:
            len_from = len(order_from)
            try:
                index_order = tuple(order_from.index(item) for item in order_to)
            except ValueError:
                raise ValueError(f"Inconsistent order definitions {order_from} and {order_to}")
        case None:
            len_from = None
            allow_skip_items = True
            return lambda key: key
        case _:
            raise ValueError(f"Invalid order specification: {reorder_indices}")

    def reorder_indices(key: Sequence):
        if not allow_skip_items and len(key) != len_from:
            raise ValueError(
                f"inconsistent index length: {len(index_order)} vs required {len(key)}"
            )
        return key.__class__(key[idx] for idx in index_order)

    return reorder_indices
