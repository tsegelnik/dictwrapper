from pytest import raises

from multikeydict.nestedmkdict import NestedMKDict
from multikeydict.tools import remap_items


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

    c = 0
    for i1 in "123":
        for i2 in "abc":
            for i3 in "xyz":
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
                            d_renamed_reordered_skipped_target_match[
                                "z2", i2new, i1
                            ] = c
                else:
                    d_renamed_match[i1, i2new, i3] = c
                    d_renamed_reordered_match[i3, i2new, i1] = c
                    if i2new != "a":
                        d_renamed_reordered_skipped_target_match[i3, i2new, i1] = c
                    if i2 != "b":
                        d_renamed_reordered_skipped_source_match[i3, i2new, i1] = c
                        if i2new != "a":
                            d_renamed_reordered_skipped_both_match[i3, i2new, i1] = c

                c += 1

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
