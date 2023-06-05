from .classwrapper import ClassWrapper
from .visitor import MakeNestedMKDictVisitor, NestedMKDictVisitor
from .nestedmkdictaccess import NestedMKDictAccess
from .flatmkdict import FlatMKDict

from typing import Any, Optional, Tuple, Generator, Sequence, Mapping, MutableMapping
class NestedMKDict(ClassWrapper):
    """Dictionary wrapper managing nested dictionaries
        The following functionality is implemented:
        - Tuple keys are treated to access nested dictionaries ('key1', 'key2', 'key3')
        - Optionally sep symbol may be set to automatically split string keys into tuple keys:
          'key1.key2.key3' will be treated as a nested key if '.' is set for the sep symbol
        - self._ may be used to access nested dictionaries via attributes: dw.key1.key2.key3
    """
    __slots__ = ('_sep', '_parent', '_types', '_not_recursive_to_others')
    _sep: str
    _parent: Any
    _not_recursive_to_others: bool
    def __new__(cls, dic: MutableMapping={}, *args, **kwargs):
        if not isinstance(dic, (MutableMapping, NestedMKDict)):
            return dic
        return ClassWrapper.__new__(cls)

    def __init__(self, dic: Optional[MutableMapping]=None, *, sep: Optional[str]=None, parent: Optional[Any]=None, recursive_to_others: bool=False):
        if dic is None:
            dic = {}
        if isinstance(dic, NestedMKDict):
            if sep is None:
                sep = dic._sep
            recursive_to_others = not dic._not_recursive_to_others
            dic = dic._object
        super().__init__(dic, types=type(dic))

        self._sep = sep
        self._not_recursive_to_others = not recursive_to_others
        self._parent = parent
        if parent:
            if sep and sep!=parent._sep:
                raise ValueError(f'Inconsistent separators: {sep} (self) and {parent._sep} (parent)')

            self._sep = parent._sep
            self._types = parent._types
            self._not_recursive_to_others = parent._not_recursive_to_others

    @property
    def _(self):
        return NestedMKDictAccess(self)

    @property
    def parent(self) -> Optional["NestedMKDict"]:
        return self._parent

    @property
    def parent_key(self):
        if not self._parent:
            return None
        for key, value in self._parent.items():
            if isinstance(value, NestedMKDict) and value.object is self.object:
                return key

        raise RuntimeError("Parent key not identified")

    def get_parent(self, level: int=1) -> Optional["NestedMKDict"]:
        if level==0:
            return self
        elif level<0:
            raise ValueError('get_parent: level should be >=0')

        current = self
        for _ in range(level):
            newcurrent = current.parent
            if newcurrent is None:
                return current
            current = newcurrent

        return current

    def child(self, key, *args, type=None, **kwargs):
        try:
            ret = self(key)
        except KeyError:
            if type is None:
                type = self._types
            self[key] = (ret:=type(*args, **kwargs))
            return self._wrap(ret, parent=self)

        if not isinstance(ret, self._wrapper_class):
            raise KeyError(f'Child {key!s} is not NestedMKDict')

        return ret

    def __call__(self, key):
        if key==():
            return self
        head, rest=self.splitkey(key)

        try:
            sub = self._object[head]
        except KeyError as e:
            raise KeyError(key) from e

        if rest:
            sub = self._wrap(sub, parent=self)
            if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
                raise TypeError(f"Nested value for '{key}' has wrong type")

            try:
                return sub(rest)
            except KeyError as e:
                raise KeyError(key) from e

        if not isinstance(sub, (ClassWrapper, self._types)):
            raise TypeError(f"Invalid value type {type(sub)} for key {key}. Expect mapping. ")

        return self._wrap_(sub, parent=self)

    def keys(self):
        return self._object.keys()

    def iterkey(self, key):
        if isinstance(key, str):
            if self._sep:
                yield from key.split(self._sep)
            else:
                yield key
        elif isinstance(key, Sequence):
            for sk in key:
                yield from self.iterkey(sk)
        else:
            yield key

    def splitkey(self, key) -> Any:
        it = self.iterkey(key)
        try:
            return next(it), tuple(it)
        except StopIteration:
            return None, None

    def any(self, key, *, object: bool=False) -> Any:
        if key==():
            return self
        head, rest=self.splitkey(key)

        try:
            sub = self._object.__getitem__(head)
        except KeyError as e:
            raise KeyError(f"No nested key '{key}'") from e

        if not rest:
            if object:
                return sub
            sub = self._wrap(sub, parent=self)
            return sub

        sub = self._wrap(sub, parent=self)
        if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
            raise TypeError(f"Nested value for '{key}' has wrong type")

        try:
            return sub.any(rest, object=object)
        except KeyError as e:
            raise KeyError(key) from e

    def get(self, key, default=None):
        if key==():
            raise TypeError("May not return self")

        head, rest=self.splitkey(key)

        if head not in self._object:
            if rest:
                raise KeyError(key)
            else:
                return default

        sub = self._object.get(head)
        if rest:
            sub = self._wrap(sub, parent=self)
            if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
                raise TypeError(f"Nested value for '{key}' has wrong type")

            return sub.get(rest, default)

        if isinstance(sub, (ClassWrapper, self._types)):
            raise TypeError(f"Invalid value type {type(sub)} for key {key}. Expect non-mapping.")

        return sub

    def __getitem__(self, key) -> Any:
        if key==():
            raise TypeError("May not return self")

        head, rest=self.splitkey(key)

        try:
            sub = self._object.__getitem__(head)
        except KeyError as e:
            raise KeyError(key) from e

        if rest:
            sub = self._wrap(sub, parent=self)
            if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
                raise TypeError(f"Nested value for '{key}' has wrong type")

            try:
                return sub[rest]
            except KeyError as e:
                raise KeyError(key) from e

        if isinstance(sub, (ClassWrapper, self._types)):
            raise TypeError(f"Invalid value type {type(sub)} for key {key}. Expect non-mapping.")
        return sub

    def pop(self, key, *, delete_parents: bool=False):
        if key==():
            raise ValueError('May not delete itself')
        key, rest=self.splitkey(key)

        sub = self._wrap(self._object.__getitem__(key), parent=self)
        if not rest:
            return self._object.pop(key)

        if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
            raise TypeError(f"Nested value for '{key}' has wrong type")

        ret = sub.pop(rest)
        if delete_parents and not sub:
            del self._object[key]
        return ret

    def delete_with_parents(self, key):
        self.pop(key, delete_parents=True)

    def __delitem__(self, key):
        if key==():
            raise ValueError('May not delete itself')
        key, rest=self.splitkey(key)

        sub = self._wrap(self._object.__getitem__(key), parent=self)
        if not rest:
            del self._object[key]
            return

        if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
            raise TypeError(f"Nested value for '{key}' has wrong type")

        del sub[rest]

    def setdefault(self, key, value) -> Any:
        key, rest=self.splitkey(key)

        if not rest:
            ret=self._object.setdefault(key, value)
            return self._wrap(ret, parent=self)

        if key in self:
            sub = self._wrap(self._object.get(key), parent=self)
        else:
            sub = self._object[key] = self._types()
            sub = self._wrap(sub, parent=self)
            # # cfg._set_parent( self )

        if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
            raise TypeError(f"Nested value for '{key}' has wrong type")

        return sub.setdefault(rest, value)

    def set(self, key, value):
        key, rest=self.splitkey(key)

        if not rest:
            self._object[key] = value
            return value

        if key in self:
            sub = self._wrap(self._object.get(key), parent=self)
        else:
            sub = self._object[key] = self._types()
            sub = self._wrap(sub, parent=self)
            # # cfg._set_parent( self )

        if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
            raise TypeError(f"Nested value for '{key}' has wrong type")

        return sub.__setitem__(rest, value)

    __setitem__= set

    def __contains__(self, key):
        if key==():
            return True
        key, rest=self.splitkey(key)

        if key not in self._object:
            return False

        if rest:
            sub = self._wrap(self._object.get(key), parent=self)

            if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
                raise TypeError(f"Nested value for '{key}' has wrong type")

            return rest in sub

        return True

    def items(self):
        for k, v in self._object.items():
            yield k, self._wrap(v, parent=self)

    def values(self):
        for v in self._object.values():
            yield self._wrap(v, parent=self)

    def copy(self) -> 'NestedMKDict':
        return NestedMKDict(self.object.copy(), parent=self._parent, sep=self._sep, recursive_to_others=not self._not_recursive_to_others)

    def deepcopy(self) -> 'NestedMKDict':
        new = NestedMKDict(self._types(), parent=self._parent, sep=self._sep, recursive_to_others=not self._not_recursive_to_others)
        for k, v in self.items():
            k = k,
            if isinstance(v, self._wrapper_class):
                new[k] = v.deepcopy()._object
            else:
                new[k] = v

        new._sep = self._sep

        return new

    def walkitems(self, startfromkey=(), *, appendstartkey=False, maxdepth=None):
        v0 = self.any(startfromkey)
        k0 = tuple(self.iterkey(startfromkey))

        if maxdepth is None:
            nextdepth=None
        else:
            nextdepth=max(maxdepth-len(k0)-1, 0)

        if maxdepth==0 or not isinstance(v0, self._wrapper_class):
            if appendstartkey:
                yield k0, v0
            else:
                yield (), v0
            return

        if not appendstartkey:
            k0 = ()

        for k, v in v0.items():
            k = k0+(k,)
            if isinstance(v, self._wrapper_class):
                for k1, v1 in v.walkitems(maxdepth=nextdepth):
                    yield k+k1, v1
            elif not self._not_recursive_to_others and isinstance(v, Mapping):
                for k1, v1 in v.items():
                    if isinstance(k1, tuple):
                        yield k+k1, v1
                    else:
                        yield k+(k1,), v1
            else:
                yield k, v

    def walkdicts(self, *, yieldself=False, ignorekeys: Sequence=()):
        for k, v in self.items():
            if k in ignorekeys:
                continue
            k = k,
            if isinstance(v, self._wrapper_class):
                yieldself=False
                for k1, v1 in v.walkdicts(yieldself=True, ignorekeys=ignorekeys):
                    yield k+k1, v1
        if yieldself:
            yield (), self

    def walkkeys(self, *args, **kwargs):
        for k, _ in self.walkitems(*args, **kwargs):
            yield k

    def walkjoinedkeys(self, *args, sep: Optional[str]=None, **kwargs) -> Generator[str, None, None]:
        if sep is None:
            sep = self._sep
        if sep is None:
            sep = '.'
        for k, _ in self.walkitems(*args, **kwargs):
            yield sep.join(k)

    def walkjoineditems(self, *args, sep: Optional[str]=None, **kwargs) -> Generator[Tuple[str, Any], None, None]:
        if sep is None:
            sep = self._sep
        if sep is None:
            sep = '.'
        for k, v in self.walkitems(*args, **kwargs):
            yield sep.join(k), v

    def walkvalues(self, *args, **kwargs):
        for _, v in self.walkitems(*args, **kwargs):
            yield v

    def visit(self, visitor, parentkey=()) -> NestedMKDictVisitor:
        visitor = MakeNestedMKDictVisitor(visitor)

        if not parentkey:
            visitor.start(self)

        visitor.enterdict(parentkey, self)
        for k, v in self.items():
            key = parentkey + (k,)
            if isinstance(v, self._wrapper_class):
                v.visit(visitor, parentkey=key)
            elif isinstance(v, FlatMKDict) and not self._not_recursive_to_others:
                visitor.enterdict(key, v)
                for subk, subv in v.items():
                    visitor.visit(key+subk, subv)
                visitor.exitdict(key, v)
            else:
                visitor.visit(key, v)

        visitor.exitdict(parentkey, self)

        if not parentkey:
            visitor.stop(self)

        return visitor

    def update(self, other) -> 'NestedMKDict':
        other = self._wrap(other)
        for k, v in other.walkitems():
            self[k] = v
        return self

    __ior__ = update

    def update_missing(self, other) -> 'NestedMKDict':
        other = self._wrap(other)
        for k, v in other.walkitems():
            try:
                key_already_present = k in self
            except TypeError:
                raise TypeError(f'Value for part({k}) is non nestable')
            else:
                if key_already_present:
                    raise TypeError(f'Key {k} already present')
            self[k] = v
        return self

    __ixor__ = update_missing

def walkitems(obj: NestedMKDict, *args, **kwargs):
    if isinstance(obj, NestedMKDict):
        yield from obj.walkitems(*args, **kwargs)
    else:
        yield (), obj
