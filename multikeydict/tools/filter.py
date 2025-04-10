from __future__ import annotations

from typing import TYPE_CHECKING

from multikeydict.nestedmkdict import NestedMKDict

from ..typing import Key

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from typing import Any, Generator


def filter_items(
    items: Iterable[tuple[Key, Any]], exclude: Sequence[Sequence[str] | str]
) -> Generator[tuple[Key, Any]]:
    _exclude = list({key} if isinstance(key, str) else set(key) for key in exclude)
    for key, value in items:
        if any(mask.issubset(key) for mask in _exclude):
            continue

        yield key, value


def mkfilter_items(
    mkdict: NestedMKDict, exclude: Sequence[Sequence[str] | str]
) -> NestedMKDict:
    ret = mkdict.__class__({}, sep=mkdict._sep)

    for key, value in filter_items(mkdict.walkitems(), exclude):
        ret[key] = value

    return ret

