from .nestedmkdict import NestedMKDict
from .flatmkdict import FlatMKDict

from typing import Sequence, Tuple

def _select(seq: Sequence, elems: set) -> Tuple[Tuple, Tuple]:
	selected = []
	rest = []
	for el in seq:
		if el in elems:
			selected.append(el)
		else:
			rest.append(el)
	return tuple(rest), tuple(selected)

def flatten(mkdict, selkeys: Sequence=()) -> NestedMKDict:
	selkeys_set = set(selkeys)
	newdict = mkdict._wrap({}, parent=mkdict)
	newdict._parent = None

	for key, v in mkdict.walkitems():
		keys_nested, keys_flat = _select(key, selkeys_set)
		if keys_flat:
			flatdict = newdict.get(keys_nested, None)
			if flatdict is None:
				newdict[keys_nested] = (flatdict:=FlatMKDict(((keys_flat, v),),))
			else:
				if not isinstance(flatdict, FlatMKDict):
					raise KeyError(f'Unable to flatten: {".".join(key)}')
				flatdict[keys_flat] = v
		else:
			newdict[key] = v

	return newdict
