from collections.abc import Sequence
from typing import Tuple

from .nestedmkdict import NestedMKDict
from .flatmkdict import FlatMKDict

def _select(seq: Sequence, elems_mask: set) -> Tuple[Tuple, Tuple]:
	selected = []
	rest = ()
	for i, el in enumerate(reversed(seq), 0):
		if el in elems_mask:
			selected.append(el)
		else:
			rest = tuple(seq[:len(seq)-i])
			break
	return tuple(rest), tuple(reversed(selected))

def flatten(mkdict: NestedMKDict, selkeys: Sequence=()) -> NestedMKDict:
	selkeys_set = set(selkeys)
	newdict = mkdict._wrap({}, parent=mkdict)
	newdict._parent = None

	for key, v in mkdict.walkitems():
		keys_nested, keys_flat = _select(key, selkeys_set)
		if keys_flat:
			try:
				flatdict = newdict.any(keys_nested)
			except KeyError:
				flatdict = None
			if flatdict is None:
				newdict[keys_nested] = (flatdict:=FlatMKDict(((keys_flat, v),),))
			elif isinstance(flatdict, FlatMKDict):
				flatdict[keys_flat] = v
			else:
				raise KeyError(f'Unable to flatten: {".".join(key)}')
		else:
			newdict[key] = v

	return newdict
