###############################################################################
#
#    Copyright 2009-2011, Universitat Pompeu Fabra
#
#    This file is part of Wok.
#
#    Wok is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Wok is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses
#
###############################################################################

import pickle
import json

from wok.element import Data

DEFAULT_SERIALIZER_NAME = "str"

# Deprecated, for compatibility only
class StrSerializer(object):
	def __init__(self):
		self.name = "str"

	def marshall(self, value):
		return str(value)

	def unmarshall(self, raw):
		return raw

class PickleSerializer(object):
	def __init__(self, enhanced = False):
		self.__enhanced = enhanced
		if enhanced:
			self.name = "epickle"
		else:
			self.name = "pickle"

	def marshall(self, value):
		if isinstance(value, Data):
			value = value.to_native()
		raw = pickle.dumps(value)
		return raw.replace("\n", r"\n")

	def unmarshall(self, raw):
		raw = raw.replace(r"\n", "\n")
		value = pickle.loads(raw)
		if self.__enhanced and isinstance(value, (list, dict)):
			value = DataFactory.from_native(value)
		return value

class JsonSerializer(object):
	def __init__(self, enhanced = False):
		self.__enhanced = enhanced
		if enhanced:
			self.name = "ejson"
		else:
			self.name = "json"

	def marshall(self, value):
		if isinstance(value, Data):
			value = value.to_native()
		return json.dumps(value)

	def unmarshall(self, raw):
		value = json.loads(raw)
		if self.__enhanced and isinstance(value, (list, dict)):
			value = DataFactory.from_native(value)
		return value

_SERIALIZERS = {
	"str" : StrSerializer(),
	"pickle" : PickleSerializer(False),
	"epickle" : PickleSerializer(True),
	"json" : JsonSerializer(False),
	"ejson" : JsonSerializer(True)
}

class SerializerFactory(object):
	@staticmethod
	def create(name):
		if name not in _SERIALIZERS:
			raise Exception("Unknown serializer: {0}".format(name))

		return _SERIALIZERS[name]
