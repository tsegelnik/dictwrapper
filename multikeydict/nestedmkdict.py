from __future__ import annotations

from collections.abc import Generator, Mapping, MutableMapping, Sequence
from contextlib import suppress
from typing import TYPE_CHECKING

from .classwrapper import ClassWrapper
from .flatmkdict import FlatMKDict
from .ipython import repr_pretty
from .nestedmkdictaccess import NestedMKDictAccess
from .visitor import MakeNestedMKDictVisitor, NestedMKDictVisitor

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any

    from .typing import KeyLike


class NestedMKDict(ClassWrapper):
    """Dictionary wrapper managing nested dictionaries
    The following functionality is implemented:
    - Tuple keys are treated to access nested dictionaries ('key1', 'key2', 'key3')
    - Optionally sep symbol may be set to automatically split string keys into tuple keys:
      'key1.key2.key3' will be treated as a nested key if '.' is set for the sep symbol
    - self._ may be used to access nested dictionaries via attributes: dw.key1.key2.key3
    """

    __slots__ = ("_sep", "_parent", "_types", "_not_recursive_to_others")
    _sep: str | None
    _parent: Any
    _not_recursive_to_others: bool

    def __new__(cls, dic: MutableMapping = {}, *args, **kwargs):
        if not isinstance(dic, (MutableMapping, NestedMKDict)):
            return dic
        return ClassWrapper.__new__(cls)

    def __init__(
        self,
        dic: MutableMapping | None = None,
        *,
        sep: str | None = None,
        parent: Any | None = None,
        recursive_to_others: bool = False,
    ):
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
            if sep and sep != parent._sep:
                raise ValueError(
                    f"Inconsistent separators: {sep} (self) and {parent._sep} (parent)"
                )

            self._sep = parent._sep
            self._types = parent._types
            self._not_recursive_to_others = parent._not_recursive_to_others

    def __str__(self):
        return f"NestedMKDict({list(self.keys())})"

    def __repr__(self):
        return object.__repr__(self)

    _repr_pretty_ = repr_pretty

    def _ipython_key_completions_(self) -> list[str]:
        return list(self.walkjoinedkeys(include_dicts=True))

    @classmethod
    def from_flatdict(
        cls,
        dct: Mapping[KeyLike, Any] | Iterable[tuple[KeyLike, Any]],
        *args,
        **kwargs,
    ) -> NestedMKDict:
        """Make a nested dictionary from a flat dictionary"""
        ret = NestedMKDict({}, *args, **kwargs)
        iterable = dct.items() if isinstance(dct, Mapping) else dct
        for key, value in iterable:
            ret[key] = value
        return ret

    @property
    def _(self):
        return NestedMKDictAccess(self)

    @property
    def parent(self) -> NestedMKDict | None:
        return self._parent

    @property
    def parent_key(self):
        if not self._parent:
            return None
        for key, value in self._parent.items():
            if isinstance(value, NestedMKDict) and value.object is self.object:
                return key

        raise RuntimeError("Parent key not identified")

    def get_parent(self, level: int = 1) -> NestedMKDict | None:
        if level == 0:
            return self
        elif level < 0:
            raise ValueError("get_parent: level should be >=0")

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
            self[key] = (ret := type(*args, **kwargs))
            return self._wrap(ret, parent=self)

        if not isinstance(ret, self._wrapper_class):
            raise KeyError(f"Child {key!s} is not NestedMKDict")

        return ret

    def get_dict(self, key, *, unwrap: bool = False) -> NestedMKDict:
        if key == ():
            return self
        head, rest = self.splitkey(key)

        try:
            sub = self._object[head]
        except KeyError as e:
            raise KeyError(key) from e

        if rest:
            sub = self._wrap(sub, parent=self)
            if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
                raise TypeError(
                    f"Expect nested dictionary as value for {key}, got {type(sub).__name__}"
                )

            try:
                return sub.get_dict(rest, unwrap=unwrap)
            except KeyError as e:
                raise KeyError(key) from e

        if not isinstance(sub, (ClassWrapper, self._types)):
            raise TypeError(
                f"Invalid value type {type(sub)} for key ({key}). Expect mapping. Perhaps, one should use [{key}] or .get_any({key})..."
            )

        return sub if unwrap else self._wrap_(sub, parent=self)

    __call__ = get_dict

    def keys(self):
        return self._object.keys()

    def iterkey(self, key):
        if isinstance(key, str) and self._sep:
            yield from key.split(self._sep)
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

    def joinkey(self, key: KeyLike) -> str:
        if isinstance(key, str):
            return key
        elif isinstance(key, Sequence):
            if self._sep is None:
                raise ValueError("sep is None")
            return self._sep.join(key)

        raise ValueError(f"Invalid key: {key}")

    def get(self, key, default=None):
        if key == ():
            raise TypeError("May not return self")

        head, rest = self.splitkey(key)

        if head not in self._object:
            if rest:
                raise KeyError(key)
            else:
                return default

        sub = self._object.get(head)
        if rest:
            sub = self._wrap(sub, parent=self)
            if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
                raise TypeError(f"Expect non-mapping as value for {key}, got {type(sub).__name__}")

            return sub.get(rest, default)

        if isinstance(sub, (ClassWrapper, self._types)):
            raise TypeError(
                f"Invalid value type {type(sub)} for key [{key}]. Expect non-mapping. "
                f"Perhaps, one should use ({key}) or .get_any({key})..."
            )

        return sub

    def get_value(self, key) -> Any:
        if key == ():
            raise TypeError("May not return self")

        head, rest = self.splitkey(key)

        try:
            sub = self._object.__getitem__(head)
        except KeyError as e:
            raise KeyError(f"{key}: {head}") from e

        if rest:
            sub = self._wrap(sub, parent=self)
            if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
                raise TypeError(f"Expect non-mapping as value for {key}, got {type(sub).__name__}")

            try:
                return sub.get_value(rest)
            except KeyError as e:
                failed_rest = getattr(e, "rest", rest)
                error = KeyError(f"{key}: {failed_rest}")
                with suppress(RuntimeError):
                    error.rest = (  # pyright: ignore [reportAttributeAccessIssue]
                        failed_rest
                    )
                raise error from e

        if isinstance(sub, (ClassWrapper, self._types)):
            raise TypeError(f"Invalid value type {type(sub)} for key {key}. Expect non-mapping.")
        return sub

    def get_any(self, key, *, unwrap: bool = False) -> Any:
        if key == ():
            return self
        head, rest = self.splitkey(key)

        try:
            sub = self._object.__getitem__(head)
        except KeyError as e:
            raise KeyError(f"No nested key '{key}'") from e

        if not rest:
            if unwrap:
                return sub
            sub = self._wrap(sub, parent=self)
            return sub

        sub = self._wrap(sub, parent=self)
        if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
            raise TypeError(f"Nested value for {key} has wrong type")

        try:
            return sub.get_any(rest, unwrap=unwrap) if unwrap else sub[rest]
        except KeyError as e:
            raise KeyError(key) from e

    __getitem__ = get_any

    def pop(self, key, *, delete_parents: bool = False):
        if key == ():
            raise ValueError("May not delete itself")
        key, rest = self.splitkey(key)

        sub = self._wrap(self._object.__getitem__(key), parent=self)
        if not rest:
            return self._object.pop(key)

        if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
            raise TypeError(f"Nested value for {key} has wrong type")

        ret = sub.pop(rest, delete_parents=delete_parents)
        if delete_parents and not sub:
            del self._object[key]
        return ret

    def delete_with_parents(self, key):
        self.pop(key, delete_parents=True)

    def __delitem__(self, key):
        if key == ():
            raise ValueError("May not delete itself")
        key, rest = self.splitkey(key)

        if not rest:
            del self._object[key]
            return

        if key not in self:
            raise KeyError(key)

        sub = self._wrap(self._object.__getitem__(key), parent=self)
        if isinstance(sub, NestedMKDict):
            sub.__delitem__(rest)
            return

        if self._not_recursive_to_others:
            raise TypeError(f"Nested value for {key} (sub: {rest}) has wrong type")

        sub.__delitem__(rest)

    def setdefault(self, key, value) -> Any:
        key, rest = self.splitkey(key)

        if not rest:
            ret = self._object.setdefault(key, value)
            return self._wrap(ret, parent=self)

        if key in self:
            sub = self._wrap(self._object.get(key), parent=self)
        else:
            sub = self._object[key] = self._types()
            sub = self._wrap(sub, parent=self)
            # # cfg._set_parent( self )

        if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
            raise TypeError(f"Nested value for {key} has wrong type")

        return sub.setdefault(rest, value)

    def _set(self, key, value):
        key, rest = self.splitkey(key)

        if not rest:
            self._object[key] = value
            return value

        if key in self:
            sub = self._wrap(self._object.get(key), parent=self)
        else:
            sub = self._object[key] = self._types()
            sub = self._wrap(sub, parent=self)
            # # cfg._set_parent( self )

        if isinstance(sub, NestedMKDict):
            return sub._set(rest, value)

        if self._not_recursive_to_others:
            raise TypeError(f"Nested value for {key} (sub: {rest}) has wrong type")

        return sub.__setitem__(rest, value)

    def set(self, key, value):
        return self._set(key, value)

    __setitem__ = set

    def __contains__(self, key):
        if key == ():
            return True
        key, rest = self.splitkey(key)

        if key not in self._object:
            return False

        if rest:
            sub = self._wrap(self._object.get(key), parent=self)

            if self._not_recursive_to_others and not isinstance(sub, NestedMKDict):
                raise TypeError(f"Nested value for {key} is not a nested dictionary")

            return rest in sub

        return True

    def items(self):
        for k, v in self._object.items():
            yield k, self._wrap(v, parent=self)

    def values(self):
        for v in self._object.values():
            yield self._wrap(v, parent=self)

    def copy(self) -> NestedMKDict:
        return NestedMKDict(
            self.object.copy(),
            parent=self._parent,
            sep=self._sep,
            recursive_to_others=not self._not_recursive_to_others,
        )

    def deepcopy(self) -> NestedMKDict:
        new = NestedMKDict(
            self._types(),
            parent=self._parent,
            sep=self._sep,
            recursive_to_others=not self._not_recursive_to_others,
        )
        for k, v in self.items():
            k = (k,)
            new[k] = v.deepcopy()._object if isinstance(v, self._wrapper_class) else v
        new._sep = self._sep

        return new

    def flatten(self, sep: str | None = None) -> dict[str, Any]:
        return dict(self.walkjoineditems(sep=sep))

    def walkitems(
        self,
        startfromkey=(),
        *,
        include_dicts: bool = False,
        appendstartkey: bool = False,
        maxdepth: int | None = None,
    ):
        v0 = self.get_any(startfromkey)
        k0 = tuple(self.iterkey(startfromkey))

        nextdepth = None if maxdepth is None else max(maxdepth - len(k0) - 1, 0)
        if maxdepth == 0 or not isinstance(v0, self._wrapper_class):
            if appendstartkey:
                yield k0, v0
            else:
                yield (), v0
            return

        if not appendstartkey:
            k0 = ()

        for k, v in v0.items():
            k = k0 + (k,)
            if isinstance(v, self._wrapper_class):
                if include_dicts:
                    yield k, v
                for k1, v1 in v.walkitems(include_dicts=include_dicts, maxdepth=nextdepth):
                    yield k + k1, v1
            elif not self._not_recursive_to_others and isinstance(v, Mapping):
                if include_dicts:
                    yield k, v
                for k1, v1 in v.items():
                    if isinstance(k1, tuple):
                        yield k + k1, v1
                    else:
                        yield k + (k1,), v1
            else:
                yield k, v

    def walkdicts(self, *, yieldself=False, ignorekeys: Sequence = ()):
        for k, v in self.items():
            if k in ignorekeys:
                continue
            k = (k,)
            if isinstance(v, self._wrapper_class):
                yieldself = False
                for k1, v1 in v.walkdicts(yieldself=True, ignorekeys=ignorekeys):
                    yield k + k1, v1
        if yieldself:
            yield (), self

    def keysmap(self) -> NestedMKDict:
        """
        Return a nested dictionary instance with similar structure,
        but dictionaries are replaced with tuples of their keys
        """
        return NestedMKDict.from_flatdict({k: tuple(dct.keys()) for k, dct in self.walkdicts()})

    def unique_key_parts(self) -> set[str]:
        """Return a set with all the unique set parts"""
        ret = set()
        for key in self.walkkeys():
            ret.update(key)
        return ret

    def walkkeys(self, *args, **kwargs):
        for k, _ in self.walkitems(*args, **kwargs):
            yield k

    def walkjoinedkeys(self, *args, sep: str | None = None, **kwargs) -> Generator[str, None, None]:
        if sep is None:
            sep = self._sep
        if sep is None:
            sep = "."
        for k, _ in self.walkitems(*args, **kwargs):
            yield sep.join(k)

    def walkjoineditems(
        self, *args, sep: str | None = None, **kwargs
    ) -> Generator[tuple[str, Any], None, None]:
        if sep is None:
            sep = self._sep
        if sep is None:
            sep = "."
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
                    visitor.visit(key + subk, subv)
                visitor.exitdict(key, v)
            else:
                visitor.visit(key, v)

        visitor.exitdict(parentkey, self)

        if not parentkey:
            visitor.stop(self)

        return visitor

    def update(self, other) -> NestedMKDict:
        other = self._wrap(other)
        for k, v in other.walkitems():
            self[k] = v
        return self

    __ior__ = update

    def update_missing(self, other) -> NestedMKDict:
        other = self._wrap(other)
        for k, v in other.walkitems():
            try:
                key_already_present = k in self
            except TypeError as e:
                raise TypeError(f"Value for part({k}) is non nestable") from e
            else:
                if key_already_present:
                    raise TypeError(f"Key {k} already present")
            self[k] = v
        return self

    __ixor__ = update_missing

    ########################################
    ### DagFlow: graph connection
    #
    ### NOTE: tests are located in the main DagFlow repo;
    ###       see https://git.jinr.ru/dag-computing/dag-flow
    #
    ### TODO: should we catch exceptions here explicitly?
    ########################################
    def __rshift__(self, other):
        """self >> other"""
        from dagflow.core.node_base import NodeBase
        from dagflow.core.output import Output
        from dagflow.parameters import Parameter

        for obj in self.walkvalues():
            if isinstance(obj, Output) and not obj.connected():
                obj >> other
            elif isinstance(obj, Parameter):
                out = obj.output
                if not out.connected():
                    out >> other
            elif isinstance(obj, NodeBase) and obj.outputs.len_all() == 1:
                out = obj.outputs[0]
                if not out.connected():
                    out >> other

    def __lshift__(self, other):
        """self << other"""
        from dagflow.core.node_base import NodeBase

        for obj in self.walkvalues():
            if isinstance(obj, NodeBase):
                obj << other

    def __rlshift__(self, other):
        """other << self"""
        from dagflow.core.output import Output
        from dagflow.parameters import Parameter

        if not isinstance(other, (Sequence, Generator)):
            raise RuntimeError(f"Cannot connect `{type(other)} << NestedMKDict`")

        for obj in self.walkvalues():
            if isinstance(obj, Output):
                obj << other
            elif isinstance(obj, Parameter):
                obj.output << other


def walkitems(obj: NestedMKDict | Any, *args, **kwargs):
    if isinstance(obj, NestedMKDict):
        yield from obj.walkitems(*args, **kwargs)
    else:
        yield (), obj


def walkvalues(obj: NestedMKDict | Any, *args, **kwargs):
    if isinstance(obj, NestedMKDict):
        yield from obj.walkvalues(*args, **kwargs)
    else:
        yield obj


def walkkeys(obj: NestedMKDict | Any, *args, **kwargs):
    if isinstance(obj, NestedMKDict):
        yield from obj.walkkeys(*args, **kwargs)
    else:
        yield ()
