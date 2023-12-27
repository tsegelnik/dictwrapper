from typing import Any, Callable, Sequence

from orderedset import OrderedSet

from .typing import KeyLike, TupleKey, properkey


def match_keys(
    keys_left_seq: Sequence[Sequence[KeyLike]],
    keys_right: Sequence[KeyLike],
    fcn: Callable[[int, TupleKey, TupleKey], Any],
) -> None:
    for key_right in keys_right:
        key_right_proper = properkey(key_right)
        setkey_right = OrderedSet(key_right_proper)
        for i_left, keys_left in enumerate(keys_left_seq):
            for key_left in keys_left:
                if key_left:
                    key_left_proper = properkey(key_left)
                    setkey_left = OrderedSet(key_left_proper)
                    if not setkey_right.issubset(setkey_left):
                        if setkey_left.intersection(setkey_right):
                            raise ValueError(
                                f"Unsupported LHS key {key_left_proper}. RHS key is {key_right_proper}"
                            )
                        continue
                else:
                    key_left_proper = ()

                fcn(i_left, key_left_proper, key_right_proper)
