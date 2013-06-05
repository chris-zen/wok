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

import json

from wok.element import Data, DataFactory

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