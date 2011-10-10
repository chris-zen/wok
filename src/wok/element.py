###############################################################################
#
#	 Copyright 2009-2011, Universitat Pompeu Fabra
#
#	 This file is part of Wok.
#
#	 Wok is free software: you can redistribute it and/or modify
#	 it under the terms of the GNU General Public License as published by
#	 the Free Software Foundation, either version 3 of the License, or
#	 (at your option) any later version.
#
#	 Wok is distributed in the hope that it will be useful,
#	 but WITHOUT ANY WARRANTY; without even the implied warranty of
#	 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	 GNU General Public License for more details.
#
#	 You should have received a copy of the GNU General Public License
#	 along with this program.  If not, see <http://www.gnu.org/licenses
#
###############################################################################

"""
This module contains all the classes necessary to work with
data elements, a type of enhanced maps to manage structured data.

The functions dataelement_from_json and dataelement_from_xml can convert XML and JSON strings to DataElement or DataList objects.

>>> json = {"a": "1", "b" : {"c": 2, "d" : [10,20,30] } }
>>> data = dataelement_from_json(json)
>>> print data # prints the whole data tree #doctest: +NORMALIZE_WHITESPACE
{
  b = {
	d = [
	  10
	  20
	  30
	]
	c = 2
  }
  a = 1
}


DataElement and DataList objects contain nested data that can be interrogated hierarchically:
>>> print data["b/c"] 
2
>>> print data["b/d[2]"] 
30
>>> data["x/y"] = 5
>>> print data["x"]  #doctest: +NORMALIZE_WHITESPACE
{
 y = 5
}

It is possible to specify a different node separation character (default is '/'). # TODO: is the choice of the key_sep permanent?
It is also possible to create new elements or to change the values of an item:

>>> data = DataElement(key_sep = '.')
>>> data["a.b"] = 6
>>> data["f.j.k"] = 8
>>> a_data = data["a"]
>>> print a_data  #doctest: +NORMALIZE_WHITESPACE
{
  b = 6
}
>>> print data["a.b"]
6

Note that once defined, the key_sep can not be changed. 
So, if you try to access to a item using a wrong key separator, you will get an error:
>>> print data["a/b"] #doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
	...
KeyError: 'a/b'

>>> x_data = a_data.create_element()
>>> x_data["y"] = "Hello"
>>> a_data["x"] = x_data
>>> print a_data  #doctest: +NORMALIZE_WHITESPACE
{
x = {
	y = Hello
  }
  b = 6
}

There are many more functionalities, such as:
- variables expansion
- key existence checking
- basic tree transformations
- trees merge
"""

import re
import json
from copy import deepcopy

_IDENTIFIER_PAT = re.compile("^[a-zA-Z_]+$")
_LIST_PAT = re.compile("^([a-zA-Z_]+)\[(\d+)\]$")

_DEFAULT_KEY_SEP = "."
_INDENT = "  "

def _list_ensure_index(l, index):
	list_len = len(l)
	if index >= list_len:
		l += [None] * (index + 1 - list_len)

_VARPAT = re.compile(r"\$(\{[._a-z0-9]+\}|[._a-z0-9]+)")

def _expand(key, value, context, path = None):
	if path is None:
		path = set()
	
	res = []
	last = 0
	for m in _VARPAT.finditer(value):
		name = m.group(1)
		if name[0] == "{":
			name = name[1:-1]

		start = m.start()
		end = m.end()

		res += [value[last:start]]
		
		if name not in path:
			if name in context:
				expanded_value = _expand(name, str(context[name]), context, path.union(set([name])))
			else:
				raise Exception("Undefined variable '%s' at '%s'" % (name, key))
		else:
			expanded_value = "@{%s}" % name

		res += [expanded_value]
		last = end

	res += [value[last:]]
	
	return "".join(res)

def dataelement_from_xml(xmle):
	"""
	Convert a XML string to a DataList object

#TODO: example
	"""
	elen = len(xmle)
	if elen == 0:
		return xmle.text
	else:
		tags = {}
		for e in xmle:
			if e.tag in tags:
				tags[e.tag] += [e]
			else:
				tags[e.tag] = [e]

		data = DataElement(key_sep = "/")
		for tag, elist in tags.items():
			if len(elist) == 1:
				data[tag] = dataelement_from_xml(elist[0])
			else:
				l = DataList(key_sep = "/")
				for e in elist:
					l += [dataelement_from_xml(e)]
				data[tag] = l

	return data

def dataelement_from_json(obj, key_sep='/'): 
	"""
	Converts a JSON dictionary or List to a DataElement or a DataList element respectively.

	# Example: converting a Dictionary
	>>> json_dict = {'a': {'b': [1, 2]}}
	>>> json = dataelement_from_json(json_dict)
	>>> print json #doctest: +NORMALIZE_WHITESPACE
	{
	  a = {
		b = [
		  1
		  2
		]
	  }
	}

	# Example: converting a list
	>>> json_list = [1, 2, 3]
	>>> json = dataelement_from_json(json_list)
	>>> print json
	[1, 2, 3]

	"""
	if isinstance(obj, dict):
		return DataElement(obj, key_sep = key_sep)
	elif isinstance(obj, list):
		return DataList(obj, key_sep = key_sep)
	else:
		raise Exception("Simple value can not be translated to DataElement: {}".format(obj))

def dataelement_from_json_path(path):
	f = open(path, "r")
	d = json.load(f)
	e = dataelement_from_json(d)
	f.close()
	return e

class DataElementJsonEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, DataElement):
			return obj.data
		elif isinstance(obj, DataList):
			return obj.data


class KeyPath(object):
	def __init__(self, path, sep = _DEFAULT_KEY_SEP):
		self.sep = sep
		
		if isinstance(path, list):
			self.nodes = path
		elif isinstance(path, KeyPathNode):
			self.nodes = [path]
		else:
			self.nodes = []
			splited_path = path.split(self.sep)
			for path_node in splited_path:
				self.nodes += [KeyPathNode(path_node)]

	def __len__(self):
		return len(self.nodes)
		
	def __getitem__(self, key):
		return self.nodes[key]
		
	def subpath(self, start, end = None):
		if end is None:
			return KeyPath(self.nodes[start:], sep = self.sep)
		else:
			return KeyPath(self.nodes[start:end], sep = self.sep)
		
	def __str__(self):
		return self.sep.join([str(node) for node in self.nodes])

class KeyPathNode(object):
	def __init__(self, name):
		self.name = name
		self.type = None
		self.index = None
		
		m = _LIST_PAT.match(name)
		if m is not None: # list reference
			self.name = m.group(1)
			self.index = int(m.group(2))

	def has_type(self):
		return self.type is not None
		
	def is_list(self):
		return self.index is not None
		
	def __str__(self):
		sb = [self.name]
		if self.type is not None:
			sb += ["{%s}" % self.type]
		if self.index is not None:
			sb += ["[%i]" % self.index]
		return "".join(sb)

class DataFactory(object):
	@staticmethod
	def from_native(obj, key_sep = _DEFAULT_KEY_SEP):
		if isinstance(obj, dict):
			return DataElement(obj, key_sep)
		elif isinstance(obj, list):
			return DataList(obj, key_sep)
		else:
			return obj

	@staticmethod
	def create_element(data = None, key_sep = _DEFAULT_KEY_SEP):
		return DataElement(data, key_sep = key_sep)

	@staticmethod		
	def create_list(data = None, key_sep = _DEFAULT_KEY_SEP):
		return DataList(data, key_sep = key_sep)

class Data(object):
	def __init__(self, key_sep = _DEFAULT_KEY_SEP):
		self.key_sep = key_sep

	def _path(self, key):
		if key is None:
			raise KeyError("None key")

		if isinstance(key, KeyPath):
			path = key
		else:
			path = KeyPath(key, sep = self.key_sep)

		if len(path) == 0:
			raise KeyError("Empty key")

		return path

	def _wrap(self, obj):
		if isinstance(obj, dict):
			return DataElement(obj, self.key_sep)
		elif isinstance(obj, list):
			return DataList(obj, self.key_sep)
		else:
			return obj
	
	def _from_list(self, data, lst):
		for e in lst:
			data += [self._wrap(e)]

	def _from_dict(self, data, dic):
		for k, v in dic.items():
			data[k] = self._wrap(v)

	def _create_element(self, data = None):
		return DataElement(data, key_sep = self.key_sep)
		
	def _create_list(self, data = None):
		return DataList(data, key_sep = self.key_sep)

	def clone(self):
		return deepcopy(self)

	def _repr_level_object(self, sb, level, v):
		if isinstance(v, DataElement) or isinstance(v, DataList):
			v.repr_level(sb, level)
		else:
			sb += [str(v)]
			
	def repr_level(self, sb, level):
		raise Exception("Unimplemented method")

	def __repr__(self):
		return "".join(self.repr_level([], 0))

class DataValue(Data): # not used
	def __init__(self, value, key_sep = _DEFAULT_KEY_SEP):
		Data.__init__(self, key_sep)
		self.value = value

	def __repr__(self):
		return str(self.value)

class DataList(Data):
	def __init__(self, obj = None, key_sep = _DEFAULT_KEY_SEP):
		Data.__init__(self, key_sep)
		
		self.data = []
		if obj is not None and isinstance(obj, list):
			self._from_list(self.data, obj)

	def __len__(self):
		return len(self.data)
		
	def __repr__(self):
		return str(self.data)

	def __getitem__(self, key):
		if isinstance(key, int):
			return self.data[key]
		else:
			path = self._path(key)
			p0 = path[0]
			if not p0.is_list():
				raise TypeError("list indices must be integers, not '{}'".format(p0.name))

			if p0.index >= len(self.data):
				raise IndexError(p0.index)

			obj = self.data[p0.index]
			if obj is None:
				return None

			if len(path) == 1:
				return obj
			else:
				return obj[key.subpath(1)]
		
	def __setitem__(self, key, value):
		if isinstance(key, int):
			self.data[key] = value
		else:
			path = self._path(key)
			p0 = path[0]
			if not p0.is_list():
				raise TypeError("list indices must be integers, not '{}'".format(p0.name))

			self.ensure_index(p0.index)
			obj = self.data[p0.index]
			if obj is None:
				self.data[p0.index] = obj = DataElement(key_sep = self.key_sep)

			obj[key.subpath(1)] = value
	
	def __delitem__(self, key):
		del self.data[key]
		
	def __iter__(self):
		return iter(self.data)

	def __iadd__(self, value):
		self.data += value
		return self

	def append(self, value):
		self.data.append(value)

	def remove(self, value):
		self.data.remove(value)

	def ensure_index(self, index):
		list_len = len(self.data)
		if index >= list_len:
			self.data += [None] * (index + 1 - list_len)

	def merge(self, e):
		if not (isinstance(e, DataList) or isinstance(e, list)):
			raise Exception("A data element list cannot merge an element of type " % type(e))

		for d in e:
			self.data += [d]

	def expand_vars(self, context, path = None):
		if path is None:
			path = list()

		key = ".".join(path)

		for i in xrange(len(self.data)):
			data = self.data[i]
			if isinstance(data, Data):
				data.expand_vars(context, path + ['[%i]' % i])
			elif isinstance(data, str) or isinstance(data, unicode):
				self.data[i] = _expand(key, data, context)

	def to_native(self):
		native = []
		for data in self.data:
			if isinstance(data, Data):
				value = data.to_native()
			else:
				value = data
			native += [value]
		return native
			
	def repr_level(self, sb, level):
		sb += ["[\n"]
		level += 1
		for e in self.data:
			sb += [_INDENT * level]
			self._repr_level_object(sb, level, e)
			sb += ["\n"]
		level -= 1
		sb += [_INDENT * level]
		sb += ["]"]

# for backward compatibility only
class DataElementList(DataList):
	pass

class DataElement(Data):
	def __init__(self, obj = None, key_sep = _DEFAULT_KEY_SEP):
		Data.__init__(self, key_sep)
		
		self.data = {}
		if obj is not None and isinstance(obj, dict):
			self._from_dict(self.data, obj)

	def keys(self):
		return self.data.keys()

	def __len__(self):
		return len(self.data)

	def __getitem__(self, key):
		path = self._path(key)
		p0 = path[0]
		obj = self.data[p0.name]
		if p0.is_list():
			obj = obj[p0.index]
		
		if len(path) == 1:
			return obj
		else:
			#if p0.is_list():
			#	return obj[path]
			#else:
			return obj[path.subpath(1)]

	def __setitem__(self, key, value):
		path = self._path(key)
		p0 = path[0]
		
		if len(path) == 1:
			if p0.is_list():
				lst = self.data[p0.name]
				_list_ensure_index(lst, p0.index)
				lst[p0.index] = value
			else:
				self.data[p0.name] = value
		else:
			if p0.name not in self.data:
				if p0.is_list():
					self.data[p0.name] = DataList(key_sep = self.key_sep)
				else:
					self.data[p0.name] = DataElement(key_sep = self.key_sep)

			if p0.is_list():
				#TODO check that self.data[p0.name] is a list
				self.data[p0.name][path] = value
			else:
				self.data[p0.name][path.subpath(1)] = value

	def __delitem__(self, key):
		path = self._path(key)
		p0 = path[0]
		
		if len(path) == 1:
			if p0.is_list():
				lst = self.data[p0.name]
				_list_ensure_index(lst, p0.index)
				lst[p0.index] = None
			else:
				del self.data[p0.name]
		else:
			obj = self.data[p0.name]
			del obj[path.subpath(1)]
	
	def __iter__(self):
		return iter(self.data)

	def __contains__(self, key):
		path = self._path(key)
		p0 = path[0]
		key_in_data = p0.name in self.data
		
		if len(path) == 1:
			if p0.is_list():
				return key_in_data and p0.index < len(self.data[p0.name])
			else:
				return key_in_data
		elif key_in_data:
			obj = self.data[p0.name]
			if p0.is_list():
				key_in_data = isinstance(obj, (DataList, list))
				return key_in_data and path in obj
			else:
				key_in_data = isinstance(obj, (DataElement, dict))
				return key_in_data and path.subpath(1) in obj
		else:
			return False

	def items(self):
		return self.data.items()
	
	def iteritems(self):
		return self.data.iteritems()

	def repr_level(self, sb, level):
		sb += ["{\n"]
		level += 1
		keys = self.data.keys()
		keys.sort(reverse = True)
		for k in keys:
			v = self.data[k]
			sb += [_INDENT * level]
			sb += ["%s = " % k]
			self._repr_level_object(sb, level, v)
			sb += ["\n"]
		level -= 1
		sb += [_INDENT * level]
		sb += ["}"]

		return sb

	def get(self, key, default=None, dtype=None):
		if not key in self:
			return default

		value = self[key]
		if dtype == bool and not isinstance(value, bool):
			bool_map = {
				"0" : False, "1" : True,
				"no" : False, "yes" : True,
				"false" : False, "true" : True }
			value = str(value).lower()
			if value not in bool_map:
				return default
			return bool_map[value]
		else:
			if dtype is not None:
				return dtype(value)
			else:
				return value

	def create_element(self, key = None, data = None):
		e = Data._create_element(self, data)
		if key is not None:
			self[key] = e
		return e

	def create_list(self, key = None, data = None):
		l = Data._create_list(self, data)
		if key is not None:
			self[key] = l
		return l

	def transform(self, nodes):
		e = DataElement(key_sep = self.key_sep)

		for ref in nodes:
			if isinstance(ref, str):
				key = path = ref
			else:
				key = ref[0]
				path = ref[1]
			
			if path in self:
				e[key] = self[path]

		return e
		
	def copy_from(self, e, keys = None):
		if keys is None:
			keys = e.keys()

		for key in keys:
			self[key] = deepcopy(e[key])

	def merge(self, e, keys = None):
		if not (isinstance(e, DataElement) or isinstance(e, dict)):
			raise Exception("A data element cannot merge an element of type " % type(e))

		if keys is None:
			keys = e.keys()

		for key in keys:
			ed = e[key]
			if key not in self.data:
				self.data[key] = deepcopy(ed)
			else:
				d = self.data[key]
				if isinstance(d, Data):
					d.merge(ed)
				else:
					self.data[key] = deepcopy(ed)

	def missing_fields(self, keys):
		missing = []
		for key in keys:
			if key not in self:
				missing += [key]
		return missing

	def check_keys(self, keys):
		missing_keys = self.missing_fields(keys)
		if len(missing_keys) > 0:
			raise MissingKeys(missing_keys)

	def expand_vars(self, context = None, path = None):
		if context is None:
			context = self

		if path is None:
			path = list()

		for key, data in self.data.iteritems():
			current_path = path + [key]
			if isinstance(data, Data):
				data.expand_vars(context, current_path)
			elif isinstance(data, str) or isinstance(data, unicode):
				self.data[key] = _expand(".".join(current_path), data, context)

	def to_native(self):
		native = {}
		for key, data in self.data.iteritems():
			if isinstance(data, Data):
				value = data.to_native()
			else:
				value = data
			native[key] = value
		return native
