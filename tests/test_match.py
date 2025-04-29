from itertools import product

from pytest import raises

from nestedmapping.tools import match_keys


def test_match():
    i1 = ("1", "2", "3")
    i2 = ("A", "B", "C")
    i3 = ("x", "y", "z")

    right = tuple((a, b) for a, b in product(i1, i2))
    left = tuple((a,) for a, in i2)

    right_extra = tuple((a, b) for a, b in product(i1, i2))
    left_extra = tuple((a, b) for a, b in product(i1, i3))

    def fcn_skip(i, key_left, key_right):
        print(f"skip {i} {key_left} {key_right}")

    print("left")
    print(left)

    print("right")
    print(right)

    print("left_extra")
    print(left_extra)

    print("right_extra")
    print(right_extra)

    print("left, right")
    match_keys((left,), right, print, fcn_skip=fcn_skip)
    print()

    print("left+(), right")
    match_keys((left, ((),)), right, print, fcn_skip=fcn_skip)
    print()

    print("left+left, right")
    match_keys((left, left), right, print, fcn_skip=fcn_skip)
    print()

    print("left+right, right")
    match_keys((left, right), right, print, fcn_skip=fcn_skip)
    print()

    print("left extra, right extra")
    match_keys(
        (left_extra,),
        right_extra,
        print,
        require_all_left_keys_processed=False,
        require_all_right_keys_processed=False,
        fcn_skip=fcn_skip,
    )
    print()

    print("left, right extra")
    match_keys(
        (left,),
        right_extra,
        print,
        require_all_left_keys_processed=False,
        require_all_right_keys_processed=False,
        fcn_skip=fcn_skip,
    )
    print()

    with raises(ValueError):
        match_keys((left_extra,), right_extra, print)
