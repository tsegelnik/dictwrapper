from typing import Any

class ClassWrapper(object):
    _object: Any
    _types: Any
    def __init__(self, obj, *, parent=None, types=None):
        self._object = obj
        if types:
            self._types = types
        else:
            self._types = type(obj)
        self._wrapper_class = type(self)

    @property
    def object(self) -> Any:
        return self._object

    def __str__(self):
        return str(self._object)

    def __repr__(self):
        return repr(self._object)

    def __dir__(self):
        return dir(self._object)

    def __len__(self):
        return len(self._object)

    def __bool__(self):
        return bool(self._object)

    def __contains__(self, v):
        return v in self._object

    def __eq__(self, other):
        if isinstance(other, ClassWrapper):
            return self._object==other._object

        return self._object==other

    def _wrap(self, obj):
        if isinstance(obj, ClassWrapper):
            return obj

        if isinstance(obj, self._types):
            return self._wrapper_class(obj, parent=self)

        return obj

