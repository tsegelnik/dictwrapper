from typing import Any


class ClassWrapper:
    __slots__ = ("_object", "_types", "_wrapper_class")
    _object: Any
    _types: Any
    _wrapper_class: Any

    def __init__(self, obj, *, types=None):
        self._object = obj
        self._types = type(obj) if types is None else types
        self._wrapper_class = type(self)

    @property
    def object(self) -> Any:
        return self._object

    def __str__(self) -> str:
        return str(self._object)

    def __repr__(self) -> str:
        return repr(self._object)

    def __dir__(self) -> list[str]:
        return dir(self._object)

    def __len__(self) -> int:
        return len(self._object)

    def __bool__(self) -> bool:
        return bool(self._object)

    def __contains__(self, v) -> bool:
        return v in self._object

    def __eq__(self, other) -> bool:
        if isinstance(other, ClassWrapper):
            return self._object == other._object

        return self._object == other

    def _wrap(self, obj, **kwargs) -> Any:
        if isinstance(obj, ClassWrapper):
            return obj

        if isinstance(obj, self._types):
            return self._wrapper_class(obj, **kwargs)

        return obj

    def _wrap_(self, obj, **kwargs) -> Any:
        return self._wrapper_class(obj, **kwargs)
