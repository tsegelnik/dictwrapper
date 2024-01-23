from itertools import product

from pytest import raises

from multikeydict.match import match_keys


def test_match():
    i1 = ("1", "2", "3")
    i2 = ("A", "B", "C")
    i3 = ("x", "y", "z")

    left = tuple((a, b) for a, b in product(i1, i2))
    right = tuple((a,) for a, in i2)

    left_bad = tuple((a, b) for a, b in product(i1, i2))
    right_bad = tuple((a, b) for a, b in product(i1, i3))

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

    print('left bad, right bad')
    match_keys(
        (left_bad,),
        right_bad,
        print,
        require_all_left_keys_processed=False,
        require_all_right_keys_processed=False,
    )

    print('left bad, right bad')
    match_keys(
        (left,),
        right_bad,
        print,
        require_all_left_keys_processed=False,
        require_all_right_keys_processed=False
    )

    with raises(ValueError):
        match_keys((left_bad,), right_bad, print)

    with raises(ValueError):
        match_keys((left,), right_bad, print)
