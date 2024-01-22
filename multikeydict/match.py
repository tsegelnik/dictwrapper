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
    ensure_right_keys_processed: bool = False,
    ensure_left_keys_processed: bool = False,
) -> None:
    processed_left_keys = set()
    skipped_left_keys = set()
    skipped_right_keys = []
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
                    if not setkey_right.issubset(setkey_left):
                        if ensure_left_keys_processed and key_left_proper not in processed_left_keys:
                            skipped_left_keys.add(key_left_proper)
                        continue
                else:
                    key_left_proper = ()

                fcn(i_left, key_left_proper, key_right_proper)
                right_processed = True

                if ensure_left_keys_processed:
                    try:
                        skipped_left_keys.remove(key_left_proper)
                    except KeyError:
                        pass
                    processed_left_keys.add(key_left_proper)

        if fcn_outer_after is not None:
            fcn_outer_after(key_right_proper)

        if not right_processed:
            skipped_right_keys.append(key_right_proper)

    if ensure_left_keys_processed and skipped_left_keys:
        raise ValueError(f"match_keys: there were unprocessed left keys {skipped_left_keys!s}")

    if ensure_right_keys_processed and skipped_right_keys:
        raise ValueError(f"match_keys: there were unprocessed right keys {skipped_right_keys!s}")
