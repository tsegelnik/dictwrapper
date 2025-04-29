from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any

from ordered_set import OrderedSet

from ..typing import Key, KeyLike, TupleKey, properkey, setkey

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence


def match_keys(
    keys_left_seq: Sequence[Sequence[KeyLike]],
    keys_right: Iterable[KeyLike],
    fcn: Callable[[int, TupleKey, TupleKey], Any],
    *,
    fcn_outer_before: Callable[[TupleKey], Any] | None = None,
    fcn_outer_after: Callable[[TupleKey], Any] | None = None,
    fcn_skip: Callable[[int, TupleKey, TupleKey], Any] | None = None,
    left_in_right: bool = True,
    right_in_left: bool = True,
    require_all_right_keys_processed: bool = True,
    require_all_left_keys_processed: bool = True,
    skippable_left_keys_should_contain: Sequence[KeyLike] | None = None,
) -> None:
    if isinstance(keys_right, str):
        raise RuntimeError("`keys_right` should be iterable, but not string")
    if not keys_left_seq:
        raise RuntimeError("Left sequence is empty")

    if left_in_right and right_in_left:

        def keys_consistent(left: set, right: set) -> bool:
            return left.issubset(right) or right.issubset(left)

    elif left_in_right:

        def keys_consistent(left: set, right: set) -> bool:
            return left.issubset(right)

    elif right_in_left:

        def keys_consistent(left: set, right: set) -> bool:
            return right.issubset(left)

    else:
        raise RuntimeError("Either right_in_left or left_in_right should be True")

    skipped_right_keys = []
    processed_left_keys = set()
    skipped_left_keys = set()

    collect_skipped_left_keys = (
        require_all_left_keys_processed or skippable_left_keys_should_contain
    )

    for key_right in keys_right:
        key_right_proper = properkey(key_right)
        setkey_right = OrderedSet(key_right_proper)
        if fcn_outer_before is not None:
            fcn_outer_before(key_right_proper)

        right_processed = False
        for i_left, keys_left in enumerate(keys_left_seq):
            for key_left in keys_left:
                if key_left:
                    key_left_proper = properkey(key_left)
                    setkey_left = OrderedSet(key_left_proper)
                    if not keys_consistent(setkey_left, setkey_right):
                        if collect_skipped_left_keys and key_left_proper not in processed_left_keys:
                            skipped_left_keys.add(key_left_proper)
                        if fcn_skip:
                            fcn_skip(i_left, key_left_proper, key_right_proper)
                        continue
                else:
                    key_left_proper = ()

                fcn(i_left, key_left_proper, key_right_proper)
                right_processed = True

                if collect_skipped_left_keys:
                    with suppress(KeyError):
                        skipped_left_keys.remove(key_left_proper)
                    processed_left_keys.add(key_left_proper)

        if fcn_outer_after is not None:
            fcn_outer_after(key_right_proper)

        if not right_processed:
            skipped_right_keys.append(key_right_proper)

    if skipped_left_keys:
        if require_all_left_keys_processed:
            raise ValueError(f"match_keys: there were unprocessed left keys {skipped_left_keys!s}")
        failure, incorrectly_skipped_key = _check_skipped_keys_incorrect(
            skipped_left_keys, skippable_left_keys_should_contain
        )
        if failure:
            raise ValueError(
                f"match_keys: there were unprocessed left keys {skipped_left_keys!s}. "
                f"{incorrectly_skipped_key} should not have been skipped."
            )

    if require_all_right_keys_processed and skipped_right_keys:
        raise ValueError(f"match_keys: there were unprocessed right keys {skipped_right_keys!s}")


def _check_skipped_keys_incorrect(
    skipped_keys: Sequence[Key] | set[Key], should_contain: Sequence[KeyLike] | None
) -> tuple[bool, Key | None]:
    if not should_contain:
        return False, None

    setkeys = tuple(setkey(keypart) for keypart in should_contain)
    return next(
        (
            (True, skipped_key)
            for skipped_key in skipped_keys
            if not any(setkey.issubset(skipped_key) for setkey in setkeys)
        ),
        (False, None),
    )
