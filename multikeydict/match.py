from contextlib import suppress
from typing import Any, Callable, Iterable, Sequence, Union

from orderedset import OrderedSet

from .typing import KeyLike, TupleKey, properkey


def match_keys(
    keys_left_seq: Sequence[Sequence[KeyLike]],
    keys_right: Iterable[KeyLike],
    fcn: Callable[[int, TupleKey, TupleKey], Any],
    *,
    fcn_outer_before: Union[Callable[[TupleKey], Any], None] = None,
    fcn_outer_after: Union[Callable[[TupleKey], Any], None] = None,
    left_in_right: bool = True,
    right_in_left: bool = True,
    require_all_right_keys_processed: bool = True,
    require_all_left_keys_processed: bool = True,
) -> None:
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
                        if (
                            require_all_left_keys_processed
                            and key_left_proper not in processed_left_keys
                        ):
                            skipped_left_keys.add(key_left_proper)
                        continue
                else:
                    key_left_proper = ()

                fcn(i_left, key_left_proper, key_right_proper)
                right_processed = True

                if require_all_left_keys_processed:
                    with suppress(KeyError):
                        skipped_left_keys.remove(key_left_proper)
                    processed_left_keys.add(key_left_proper)

        if fcn_outer_after is not None:
            fcn_outer_after(key_right_proper)

        if not right_processed:
            skipped_right_keys.append(key_right_proper)

    if require_all_left_keys_processed and skipped_left_keys:
        raise ValueError(
            f"match_keys: there were unprocessed left keys {skipped_left_keys!s}"
        )

    if require_all_right_keys_processed and skipped_right_keys:
        raise ValueError(
            f"match_keys: there were unprocessed right keys {skipped_right_keys!s}"
        )
