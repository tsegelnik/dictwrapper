import pytest
from multikeydict.nestedmkdict import NestedMKDict
from multikeydict.nestedmkdict import walkitems, walkkeys, walkvalues
from pytest import raises


def test_nestedmkdict_01():
    dw = NestedMKDict({})

    assert not dw
    assert len(dw) == 0


def test_nestedmkdict_02():
    dw = NestedMKDict(dict(a=1))

    assert dw
    assert len(dw) == 1


def test_nestedmkdict_03():
    d = dict(a=1, b=2, c=3)
    dw = NestedMKDict(d)

    assert dw.get("a") == 1
    assert dw.get("b") == 2
    assert dw.get("c") == 3
    assert dw.get("d") is None
    assert dw.get("d.e") is None

    assert tuple(dw.keys()) == ("a", "b", "c")


@pytest.mark.parametrize("sep", [None, "."])
def test_nestedmkdict_04(sep):
    dct = dict(a=1, b=2, c=3, d=dict(e=4), f=dict(g=dict(h=5)))
    dct["z.z.z"] = 0
    print(dct)
    dw = NestedMKDict(dct, sep=sep)

    #
    # Test self access
    #
    assert dw.create_child(()).object is dct
    assert dw(()).object is dct

    #
    # Test wrapping
    #
    assert isinstance(dw("d"), NestedMKDict)
    assert isinstance(dw(("f", "g")), NestedMKDict)
    assert isinstance(dw["d"], NestedMKDict)
    assert isinstance(dw[("f", "g")], NestedMKDict)
    assert isinstance(dw.get_any("d", unwrap=True), dict)
    assert isinstance(dw.get_any(("f", "g"), unwrap=True), dict)

    with raises(TypeError):
        assert isinstance(dw.get_value("d",), NestedMKDict)
    with raises(TypeError):
        assert isinstance(dw.get_value(("f", "g")), NestedMKDict)
    with raises(KeyError):
        dw("i")

    #
    # Test get tuple
    #
    assert dw.get(("d", "e")) == 4
    assert dw.get(("d", "e1")) is None
    assert dw.get(("f", "g", "h")) == 5
    assert dw[("f", "g", "h")] == 5
    assert dw.get_any(("f", "g", "h"), unwrap=True) == 5
    with raises(KeyError):
        dw.get(("z", "z", "z"))

    #
    # Test getitem tuple
    #
    assert dw[("d", "e")] == 4
    with raises(KeyError):
        dw[("d", "e1")]

    assert dw[("f", "g", "h")] == 5

    with raises(KeyError):
        dw[("z", "z", "z")]
        assert False

    #
    # Test get sep
    #
    if sep:
        assert dw.get("d.e") == 4
    else:
        assert dw.get("d.e") is None

    if sep:
        with raises(KeyError):
            dw.get("z.z.z")
    else:
        assert dw.get("z.z.z") == 0

    #
    # Test getitem sep
    #
    if sep is None:
        with raises(KeyError):
            assert dw["d.e"] == 4

        with raises(KeyError):
            assert dw["f.g.h"] == 5

        with raises(KeyError):
            assert dw[("f.g", "h")] == 5

        assert dw["z.z.z"] == 0
    else:
        with raises(KeyError):
            dw["z.z.z"]

    #
    # Test contains
    #
    assert "a" in dw
    assert "a1" not in dw
    assert "d" in dw

    #
    # Test contains tuple
    #
    assert ("d", "e") in dw
    assert ("k", "e") not in dw
    assert ("f", "g", "h") in dw
    assert ("f.g.h" in dw) == bool(sep)
    assert ("z.z.z" in dw) == (not sep)

    #
    # Test parents
    #
    g = dw(("f", "g"))
    assert g.parent.parent is dw
    assert g.get_parent(0) is g
    assert g.get_parent(1) is g.parent
    assert g.get_parent(2) is dw
    assert g.get_parent(10) is dw

    #
    # Test children
    #
    m = dw.create_child(("k", "l", "m"))
    assert dw(("k", "l", "m")).object is m.object

    #
    # Test recursive setitem
    #
    dw[("k", "l", "m", "n")] = 5
    with raises(TypeError):
        dw.create_child(tuple("klmn"))
    assert dw.get(("k", "l", "m", "n")) == 5

    dw[("o.l.m.n")] = 6
    assert dw["o.l.m.n"] == 6
    if not sep:
        assert dw.object["o.l.m.n"] == 6

    #
    # Test attribute access
    #
    assert dw._.a == 1
    assert dw._.b == 2
    assert dw._.c == 3
    assert dw._.d.e == 4
    assert dw._.f.g.h == 5

    dw._.f.g.h = 6
    assert dw._.f.g.h == 6
    assert dw._._ is dw


@pytest.mark.parametrize("sep", [None, "."])
def test_nestedmkdict_04_del(sep):
    dct = dict(a=1, b=2, c=3, d=dict(e=4), f=dict(g=dict(h=5)))
    dw = NestedMKDict(dct, sep=sep)

    if sep is not None:
        del dw["d.e"]
    else:
        del dw[("d", "e")]

    assert ("d", "e") not in dw
    assert ("d") in dw

    if sep is not None:
        del dw["f.g"]
    else:
        del dw[("f", "g")]

    assert ("f", "g", "h") not in dw
    assert ("f", "g") not in dw
    assert ("f") in dw

    with raises(KeyError):
        del dw["f.g"]

def test_nestedmkdict_06_inheritance():
    dct = dict(
        [("a", 1), ("b", 2), ("c", 3), ("d", dict(e=4)), ("f", dict(g=dict(h=5, i=6)))]
    )
    dct["z.z.z"] = 0

    class NestedMKDictA(NestedMKDict):
        def count(self):
            return len(tuple(self.walkitems()))

        def depth(self):
            return max(len(k) for k in self.walkkeys())

    dw = NestedMKDictA(dct, sep=".")
    assert dw.count() == 7
    assert dw("d").count() == 1
    assert dw("f").count() == 2
    assert dw("f.g").count() == 2
    assert dw._.f._.count() == 2

    assert dw.depth() == 3
    assert dw("d").depth() == 1
    assert dw("f").depth() == 2


def test_nestedmkdict_07_delete():
    dct = {"a": 1, "b": 2, "c": 3, "d": {"e": 4}, "f": {"g": {"h": 5}}}
    dct["z.z.z"] = 0
    dw = NestedMKDict(dct)

    assert "a" in dw
    del dw["a"]
    assert "a" not in dw

    assert ("d", "e") in dw
    del dw[("d", "e")]
    assert ("d", "e") not in dw

    assert ("f", "g", "h") in dw
    del dw._.f.g.h
    assert ("f", "g", "h") not in dw
    assert ("f", "g") in dw


def test_nestedmkdict_07a_delete_with_parents():
    dct = {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": {"e": 4},
        "f": {"g": {"h": 5}},
        "i": {"j": {}, "k": {"m": {}}},
    }
    dct["z.z.z"] = 0
    dw = NestedMKDict(dct)

    assert "a" in dw
    dw.delete_with_parents("a")
    assert "a" not in dw

    assert ("d", "e") in dw
    dw.delete_with_parents(("d", "e"))
    assert ("d", "e") not in dw
    assert ("d") not in dw

    assert ("f", "g", "h") in dw
    dw.delete_with_parents(("f", "g", "h"))
    assert ("f", "g", "h") not in dw
    assert ("f", "g") not in dw
    assert ("f",) not in dw

    dw.delete_with_parents(("i", "k", "m"))
    assert ("i", "k", "m") not in dw
    assert ("i", "k") not in dw


def test_nestedmkdict_07b_pop():
    dct = {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": {"e": 4},
        "f": {"g": {"h": 5}},
        "i": {"j": {}, "k": {"m": {}}},
    }
    dct["z.z.z"] = 0
    dw = NestedMKDict(dct)

    assert "a" in dw
    assert dw.pop("a") == 1
    assert "a" not in dw

    assert ("d", "e") in dw
    assert dw.pop(("d", "e")) == 4
    assert ("d", "e") not in dw

    assert ("f", "g", "h") in dw
    assert dw.pop(("f", "g", "h")) == 5
    assert ("f", "g", "h") not in dw
    assert ("f", "g") in dw

    dw.pop(("i", "k", "m")) == {}
    assert ("i", "k", "m") not in dw
    assert ("i", "k") in dw


def test_nestedmkdict_07c_pop():
    dct = {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": {"e": 4},
        "f": {"g": {"h": 5}},
        "i": {"j": {}, "k": {"m": {}}},
    }
    dct["z.z.z"] = 0
    dw = NestedMKDict(dct)

    assert "a" in dw
    assert dw.pop("a", delete_parents=True) == 1
    assert "a" not in dw

    assert ("d", "e") in dw
    assert dw.pop(("d", "e"), delete_parents=True) == 4
    assert ("d", "e") not in dw
    assert ("d") not in dw

    assert ("f", "g", "h") in dw
    assert dw.pop(("f", "g", "h"), delete_parents=True) == 5
    assert ("f", "g", "h") not in dw
    assert ("f", "g") not in dw
    assert ("f",) not in dw

    dw.pop(("i", "k", "m"), delete_parents=True) == {}
    assert ("i", "k", "m") not in dw
    assert ("i", "k") not in dw


def test_nestedmkdict_08_create():
    dct = dict(
        [("a", 1), ("b", 2), ("c", 3), ("d", dict(e=4)), ("f", dict(g=dict(h=5)))]
    )
    dct["z.z.z"] = 0
    dw = NestedMKDict(dct, sep=".")

    dw._("i.k").l = 3
    assert dw._.i.k.l == 3

    child = dw.create_child("child")
    assert dw("child").object == {}


def test_nestedmkdict_09_dictcopy():
    dct = dict(
        [("a", 1), ("b", 2), ("c", 3), ("d", dict(e=4)), ("f", dict(g=dict(h=5)))]
    )
    dct["z"] = {}
    dw = NestedMKDict(dct, sep=".")

    dw1 = dw.deepcopy()
    for i, (k, v) in enumerate(dw1.walkdicts()):
        # print(i, k)
        assert k in dw
        assert v._object == dw(k)._object
        assert v._object is not dw(k)._object
        assert type(v._object) is type(dw(k)._object)
    assert i == 2


def test_nestedmkdict_09_walkitems():
    dct = {
        "a": 1,
        "b": 2,
        "c": 3,
        "c1": {"i": {"j": {"k": {"l": 6}}}},
        "d": {"e": 4},
        "f": {"g": {"h": 5}},
    }
    dct["z"] = {}
    dw = NestedMKDict(dct)
    dws = NestedMKDict(dct, sep=".")

    imaxlist = [5, 0, 6, 5, 5, 5, 5, 5, 5]
    for imax, maxdepth in zip(imaxlist, [None] + list(range(len(imaxlist)))):
        i = 0
        print(f"{imax=}, {maxdepth=}")
        maxk = -1
        for i, (k, v) in enumerate(dws.walkitems(maxdepth=maxdepth)):
            print(i, k, v)
            assert maxdepth is None or len(k) <= maxdepth
            maxk = max(maxk, len(k))
        print(f"{maxk=}")
        print()
        assert i == imax

    wkeys = ["a", "b", "c", "c1.i.j.k.l", "d.e", "f.g.h"]
    assert wkeys == list(dw.walkjoinedkeys())
    assert wkeys == list(dws.walkjoinedkeys())
    wkeys = [s.replace(".", "/") for s in wkeys]
    assert wkeys == list(dw.walkjoinedkeys(sep="/"))
    assert wkeys == list(dws.walkjoinedkeys(sep="/"))

    wkeys = [tuple(s.split(".")) for s in ("c1.i.j.k", "d", "f.g", "z")]
    assert wkeys == [k for k, _ in dw.walkdicts()]

    wkeys = [tuple(s.split(".")) for s in ("c1.i", "d", "f.g")]
    assert wkeys == [k for k, _ in dw.walkdicts(ignorekeys=("z", "j"))]


def test_nestedmkdict_09_walk():
    dct = dict(
        [("a", 1), ("b", 2), ("c", 3), ("d", dict(e=4)), ("f", dict(g=dict(h=5)))]
    )
    dw = NestedMKDict(dct)

    keys0 = [("a",), ("b",), ("c",), ("d", "e"), ("f", "g", "h")]
    keys1 = [k for k, v in dw.walkitems()]
    keys2 = [k for k, v in walkitems(dw)]
    keys3 = [k for k in walkkeys(dw)]
    assert keys1 == keys0
    assert keys2 == keys0
    assert keys3 == keys0
    assert next(walkitems(123)) == ((), 123)

    values0 = [1, 2, 3, 4, 5]
    values1 = [v for v in walkvalues(dw)]
    assert values0 == values1

    assert [(k, v) for k, v in dw.walkitems("a", appendstartkey=True)] == [(("a",), 1)]
    assert [(k, v) for k, v in dw.walkitems("a", appendstartkey=False)] == [((), 1)]
    assert [(k, v) for k, v in dw.walkitems("d", appendstartkey=True)] == [
        (("d", "e"), 4)
    ]
    assert [(k, v) for k, v in dw.walkitems("d", appendstartkey=False)] == [(("e",), 4)]
    assert [(k, v) for k, v in dw.walkitems(("f", "g"), appendstartkey=True)] == [
        (("f", "g", "h"), 5)
    ]
    assert [(k, v) for k, v in dw.walkitems(("f", "g"), appendstartkey=False)] == [
        (("h",), 5)
    ]


def test_nestedmkdict_10_iterkey():
    d = dict(a=1, b=2, c=3)
    dw = NestedMKDict(d)

    assert ["a"] == list(dw.iterkey("a"))
    assert ["a.b"] == list(dw.iterkey("a.b"))
    assert ["a", "b"] == list(dw.iterkey(("a", "b")))
    assert [1] == list(dw.iterkey(1))
    assert [1.0] == list(dw.iterkey(1.0))


def test_nestedmkdict_11_iterkey():
    d = dict(a=1, b=2, c=3)
    dw = NestedMKDict(d, sep=".")

    assert ["a"] == list(dw.iterkey("a"))
    assert ["a", "b"] == list(dw.iterkey("a.b"))
    assert ["a", "b"] == list(dw.iterkey(("a", "b")))
    assert [1] == list(dw.iterkey(1))
    assert [1.0] == list(dw.iterkey(1.0))


def test_nestedmkdict_setdefault_01():
    d = dict(a=dict(b=dict(key="value")))
    dw = NestedMKDict(d)

    newdict = dict(newkey="newvalue")

    sd1 = dw.setdefault(("a", "b"), newdict)
    assert isinstance(sd1, NestedMKDict)
    assert sd1._object == d["a"]["b"]

    sd2 = dw.setdefault(("a", "c"), newdict)
    assert isinstance(sd2, NestedMKDict)
    assert sd2._object == newdict


def test_nestedmkdict_eq_01():
    d = dict(a=dict(b=dict(key="value")))
    dw = NestedMKDict(d)

    assert dw("a") == d["a"]
    assert d["a"] == dw("a")
    assert dw("a") != d
    assert dw("a") == dw("a")
    assert dw("a") is not dw("a")

    assert dw.get_dict("a")==d["a"]
    assert dw.get_dict("a") is not d["a"]
    assert dw.get_dict("a", unwrap=True)==d["a"]
    assert dw.get_dict("a", unwrap=True) is d["a"]

    assert dw.get_dict(("a", "b"))==d["a"]["b"]
    assert dw.get_dict(("a", "b")) is not d["a"]["b"]
    assert dw.get_dict(("a", "b"), unwrap=True)==d["a"]["b"]
    assert dw.get_dict(("a", "b"), unwrap=True) is d["a"]["b"]

def test_nestedmkdict_keysmap():
    dct = {
        "a": 1,
        "b": 2,
        "c": 3,
        "c1": {"i": {"j": {"k": {"l": 6}}}},
        "d": {"e": 4, "f": 5, "g": 6},
    }
    km = {
            "c1": {"i": {"j": {"k": ("l",)}}},
            "d": ("e", "f", "g")
            }
    dw = NestedMKDict(dct)
    keysmap = dw.keysmap()
    assert keysmap==km

    dw2 = NestedMKDict.from_flatdict(dw.walkitems())
    assert dw2==dw

    dw3 = NestedMKDict.from_flatdict(dict(dw.walkitems()))
    assert dw3==dw
