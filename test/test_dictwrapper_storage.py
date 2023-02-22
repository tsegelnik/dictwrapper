from dictwrapper.dictwrapper import DictWrapper
from storage.storage import Storage
from pytest import raises

def test_dictwrapper_storage():
    storage = Storage({
        ('a1', 'b1', 'c1'): 'v1',
        ('a2', 'b2', 'c2'): 'v2',
        })
    dct = {'root': {
        'subfolder1': {
            'key1': 'value1',
            'key2': 'value2'
        },
        'subfolder2': {
            'key1': 'value1',
            'key2': 'value2',
            'st': storage
        },
        'key0': 'value0'
    }}
    dw = DictWrapper(dct)
    dws = DictWrapper(dct, sep='.')

    st1 = dw['root', 'subfolder2', 'st']
    assert st1 is storage
    assert st1['a1', 'b1', 'c1']=='v1'
    assert st1['b1', 'a1', 'c1']=='v1'
    assert st1['c1', 'a1', 'b1']=='v1'

    assert dw['root', 'subfolder2', 'st', 'a1', 'b1', 'c1']=='v1'
    assert dw['root', 'subfolder2', 'st', 'b1', 'a1', 'c1']=='v1'
    assert dw['root', 'subfolder2', 'st', 'c1', 'a1', 'b1']=='v1'
    assert dw['root', 'subfolder2', 'st', 'a2', 'b2', 'c2']=='v2'
    assert dw['root', 'subfolder2', 'st', 'b2', 'a2', 'c2']=='v2'
    assert dw['root', 'subfolder2', 'st', 'c2', 'a2', 'b2']=='v2'

    assert dws['root.subfolder2.st.a1.b1.c1']=='v1'
    assert dws['root.subfolder2.st.b1.a1.c1']=='v1'
    assert dws['root.subfolder2.st.c1.a1.b1']=='v1'
    assert dws['root.subfolder2.st.a2.b2.c2']=='v2'
    assert dws['root.subfolder2.st.b2.a2.c2']=='v2'
    assert dws['root.subfolder2.st.c2.a2.b2']=='v2'

    assert ('root', 'subfolder2', 'st', 'a1', 'b1', 'c1') in dw
    assert ('root', 'subfolder2', 'st', 'b1', 'a1', 'c1') in dw
    assert ('root', 'subfolder2', 'st', 'c1', 'a1', 'b1') in dw
    assert ('root', 'subfolder2', 'st', 'a2', 'b2', 'c2') in dw
    assert ('root', 'subfolder2', 'st', 'b2', 'a2', 'c2') in dw
    assert ('root', 'subfolder2', 'st', 'c2', 'a2', 'b2') in dw

    assert 'root.subfolder2.st.a1.b1.c1' in dws
    assert 'root.subfolder2.st.b1.a1.c1' in dws
    assert 'root.subfolder2.st.c1.a1.b1' in dws
    assert 'root.subfolder2.st.a2.b2.c2' in dws
    assert 'root.subfolder2.st.b2.a2.c2' in dws
    assert 'root.subfolder2.st.c2.a2.b2' in dws

    assert 'root.subfolder3.st.c2.a2.b2' not in dws
    assert 'root.subfolder2.st.c3.a2.b2' not in dws

    with raises(KeyError):
        dws['root.subfolder2.st.a1.b2.c1']

    with raises(KeyError):
        dws['root.subfolder1.st.a1.b1.c1']
