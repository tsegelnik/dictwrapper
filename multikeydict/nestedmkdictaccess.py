from __future__ import annotations

from typing import TYPE_CHECKING

from .ipython import repr_pretty

if TYPE_CHECKING:
    from .nestedmkdict import NestedMKDict


class NestedMKDictAccess:
    """NestedMKDict wrapper. Enables attribute based access to nested dictionaries"""

    __slots__ = ("_",)
    _: NestedMKDict

    def __init__(self, dct: NestedMKDict):
        object.__setattr__(self, "_", dct)

    def __str__(self):
        return str(self._)

    _repr_pretty_ = repr_pretty

    def __call__(self, key):
        return self._.child(key)._

    def __getattr__(self, key):
        if key.startswith("__") and key.endswith("__"):
            # needed for proper operation of __dir__() and ipython completion
            return object.__getattr__(self, key)

        ret = self._[key]

        if isinstance(ret, self._._wrapper_class):
            return ret._

        return ret

    def __setattr__(self, key, value):
        self._[key] = value

    def __delattr__(self, key):
        del self._[key]

    def __dir__(self):
        return list(self._.keys())
