from itertools import product

from pytest import raises

from numpy import array
from multikeydict.nestedmkdict import NestedMKDict
from multikeydict.tools import mkmap, remap_items


def test_remap_items_01():
    d_main = NestedMKDict()
    d_reordered_match = NestedMKDict()
    d_reordered_skipped_match = NestedMKDict()
    d_renamed_match = NestedMKDict()
    d_renamed_reordered_match = NestedMKDict()
    d_renamed_reordered_skipped_source_match = NestedMKDict()
    d_renamed_reordered_skipped_target_match = NestedMKDict()
    d_renamed_reordered_skipped_both_match = NestedMKDict()

    rename_indices = {
        "z": ("z1", "z2"),
        "a": ("A",),
    }
    reorder_indices = [2, 1, 0]
    reorder_indices_names = (("a", "b", "c"), ("c", "b", "a"))
    skip_indices_source = (("1", "z"), ("b",))
    skip_indices_target = (("1", "z2"), ("a",))

    for c, (i1, i2, i3) in enumerate(product("123", "abc", "xyz")):
        d_main[i1, i2, i3] = c
        d_reordered_match[i3, i2, i1] = c
        if (i1 != "1" or i3 != "z") and i2 != "b":
            d_reordered_skipped_match[i3, i2, i1] = c

        i2new = "A" if i2 == "a" else i2

        if i3 == "z":
            d_renamed_match[i1, i2new, "z1"] = c
            d_renamed_match[i1, i2new, "z2"] = c

            d_renamed_reordered_match["z1", i2new, i1] = c
            d_renamed_reordered_match["z2", i2new, i1] = c

            if i2 != "b" and i1 != "1":
                if i2new != "a":
                    d_renamed_reordered_skipped_both_match["z1", i2new, i1] = c
                    d_renamed_reordered_skipped_both_match["z2", i2new, i1] = c

                d_renamed_reordered_skipped_source_match["z1", i2new, i1] = c
                d_renamed_reordered_skipped_source_match["z2", i2new, i1] = c

            if i2new != "a":
                d_renamed_reordered_skipped_target_match["z1", i2new, i1] = c
                if i1 != "1":
                    d_renamed_reordered_skipped_target_match["z2", i2new, i1] = c
        else:
            d_renamed_match[i1, i2new, i3] = c
            d_renamed_reordered_match[i3, i2new, i1] = c
            if i2new != "a":
                d_renamed_reordered_skipped_target_match[i3, i2new, i1] = c
            if i2 != "b":
                d_renamed_reordered_skipped_source_match[i3, i2new, i1] = c
                if i2new != "a":
                    d_renamed_reordered_skipped_both_match[i3, i2new, i1] = c

    d_new = remap_items(d_main, reorder_indices=reorder_indices)
    assert d_reordered_match == d_new

    d_new = remap_items(d_main, reorder_indices=reorder_indices_names)
    assert d_reordered_match == d_new

    d_new = remap_items(
        d_main,
        reorder_indices=reorder_indices,
        skip_indices_target=skip_indices_source,
    )
    assert d_reordered_skipped_match == d_new

    d_new = remap_items(
        d_main,
        rename_indices=rename_indices,
    )
    assert d_renamed_match == d_new

    d_new = remap_items(
        d_main,
        rename_indices=rename_indices,
    )
    assert d_renamed_match == d_new

    d_new = remap_items(
        d_main,
        rename_indices=rename_indices,
        reorder_indices=reorder_indices,
    )
    assert d_renamed_reordered_match == d_new

    d_new = remap_items(
        d_main,
        rename_indices=rename_indices,
        reorder_indices=reorder_indices,
        skip_indices_target=skip_indices_target,
    )
    assert d_renamed_reordered_skipped_target_match == d_new

    d_new = remap_items(
        d_main,
        rename_indices=rename_indices,
        reorder_indices=reorder_indices,
        skip_indices_source=skip_indices_source,
    )
    assert d_renamed_reordered_skipped_source_match == d_new

    d_new = remap_items(
        d_main,
        rename_indices=rename_indices,
        reorder_indices=reorder_indices,
        skip_indices_source=skip_indices_source,
        skip_indices_target=skip_indices_target,
    )

    with raises(ValueError):
        remap_items(d_main, reorder_indices=[["a", "b", "c"], ["c", "a", "B"]])


def test_mkmap_01():
    m1 = NestedMKDict(
        {
            "a": 0,
            "b": {"c": 1},
            "d": {
                "e": {"f": 2},
            },
        }
    )

    m2 = mkmap((lambda d: -d-1), m1, sep=".")
    assert m1._sep is None
    assert m2._sep == "."

    array1 = array(list(m1.walkvalues()))
    array2 = array(list(m2.walkvalues()))
    assert all((array1)==list(range(3)))
    assert all((array2)==list(range(-1, -4, -1)))
    assert list(m1.walkkeys())==list(m2.walkkeys())

    sumfn = lambda a, b: a+b
    m3a = mkmap(sumfn, m1, m2)
    m3b = mkmap(sumfn, m1, m2, sep=False)
    m3c = mkmap(sumfn, m1, m2, sep=True)
    m3d = mkmap(sumfn, m1, m2, sep=0)
    m3e = mkmap(sumfn, m1, m2, sep=1)
    m3f = mkmap(sumfn, m1, m2, sep=-1)
    m3g = mkmap(sumfn, m1, m2, sep="/")

    assert list(m1.walkkeys())==list(m3a.walkkeys())
    assert list(m1.walkkeys())==list(m3b.walkkeys())
    assert list(m1.walkkeys())==list(m3c.walkkeys())
    assert list(m1.walkkeys())==list(m3d.walkkeys())
    assert list(m1.walkkeys())==list(m3e.walkkeys())
    assert list(m1.walkkeys())==list(m3f.walkkeys())
    assert list(m1.walkkeys())==list(m3g.walkkeys())

    assert all(array(list(m3a.walkvalues()))==-1)
    assert all(array(list(m3b.walkvalues()))==-1)
    assert all(array(list(m3c.walkvalues()))==-1)
    assert all(array(list(m3d.walkvalues()))==-1)
    assert all(array(list(m3e.walkvalues()))==-1)
    assert all(array(list(m3f.walkvalues()))==-1)
    assert all(array(list(m3g.walkvalues()))==-1)

    assert m3a._sep is None
    assert m3b._sep is None
    assert m3c._sep is None
    assert m3d._sep is None
    assert m3e._sep == "."
    assert m3f._sep == "."
    assert m3g._sep == "/"


    with raises(IndexError):
        mkmap(sumfn, m1, m2, sep=2)

    with raises(IndexError):
        mkmap(sumfn, m1, m2, sep=-2)

    with raises(TypeError):
        mkmap(sumfn, m1, m2, sep=-2.0)
