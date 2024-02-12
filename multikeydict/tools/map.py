from __future__ import annotations

from typing import TYPE_CHECKING

from ..typing import setkey

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from typing import Any

    from ..nestedmkdict import NestedMKDict
    from ..typing import KeyLike


def remap_items(
    source: NestedMKDict,
    target: NestedMKDict,
    *,
    indices: Mapping[str, Sequence[str]] | None = None,
    skip_indices: Sequence[KeyLike | set[str]] | None = None,
    fcn: Callable[[Any], Any] = lambda o: o,
) -> None:
    from itertools import product

    if skip_indices is not None:
        skip_sets = tuple(sq if isinstance(sq, set) else setkey(sq) for sq in skip_indices)
        skip = lambda key: any(ss.issubset(key) for ss in skip_sets)
    else:
        skip = lambda _: False
    if indices is not None:
        for key, value in source.walkitems():
            for newkey in product(*tuple(indices.get(skey, (skey,)) for skey in key)):
                if skip(newkey):
                    continue
                target[newkey] = fcn(value)
    else:
        for key, value in source.walkitems():
            if skip(key):
                continue
            target[key] = fcn(value)
