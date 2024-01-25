from itertools import product

from pytest import raises

from multikeydict.match import match_keys


def test_match():
    i1 = ("1", "2", "3")
    i2 = ("A", "B", "C")
    i3 = ("x", "y", "z")

    right = tuple((a, b) for a, b in product(i1, i2))
    left  = tuple((a,) for a, in i2)

    right_extra = tuple((a, b) for a, b in product(i1, i2))
    left_extra  = tuple((a, b) for a, b in product(i1, i3))

    print('left, right')
    match_keys((left,), right, print)
    print()

    print('left+(), right')
    match_keys((left, ((),)), right, print)
    print()

    print('left+left, right')
    match_keys((left, left), right, print)
    print()

    print('left+right, right')
    match_keys((left, right), right, print)
    print()

    print('left extra, right extra')
    match_keys(
        (left_extra,),
        right_extra,
        print,
        require_all_left_keys_processed=False,
        require_all_right_keys_processed=False,
    )
    print()

    print('left, right extra')
    match_keys(
        (left,),
        right_extra,
        print,
        require_all_left_keys_processed=False,
        require_all_right_keys_processed=False
    )
    print()

    with raises(ValueError):
        match_keys((left_extra,), right_extra, print)

