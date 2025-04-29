from itertools import product

from nestedmapping.tools import filter_items


def test_filter():
    i1 = ("1", "2", "3")
    i2 = ("A", "B", "C")
    i3 = ("x", "y", "z")

    items = tuple((v, k) for k, v in enumerate(tuple(product(i1, i2, i3))))

    items1 = tuple(filter_items(items, []))
    assert items1 == items

    items2 = tuple(filter_items(items, ["z"]))
    items2_check = tuple((k, v) for k, v in items if "z" not in k)
    assert items2 == items2_check

    items3 = tuple(filter_items(items, ["z", "B"]))
    items3_check = tuple((k, v) for k, v in items if "z" not in k and "B" not in k)
    assert items3 == items3_check

    items4 = tuple(filter_items(items, [("1", "z"), ("x", "B", "2")]))
    items4_check = tuple(
        (k, v)
        for k, v in items
        if not ("z" in k and "1" in k)
        and not ("B" in k and "x" in k and "2" in k)
    )
    assert items4 == items4_check

    items5 = tuple(filter_items(items, [("1", "z"), ("B", "x", "2")]))
    items5_check = tuple(
        (k, v)
        for k, v in items
        if not ("z" in k and "1" in k)
        and not ("B" in k and "x" in k and "2" in k)
    )
    assert items5 == items5_check

    items5 = tuple(filter_items(items, [[]]))
    items5_check = ()
    assert items5 == items5_check
