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

from wok.element import DataFactory

class PickleSerializer(object):
	def __init__(self, enhanced = False):
		self.__enhanced = enhanced
		if enhanced:
			self.name = "epickle"
		else:
			self.name = "pickle"

	def marshall(self, value):
#		if isinstance(value, Data):
#			value = value.to_native()
		raw = pickle.dumps(value)
		return raw.replace("\n", r"\n")

	def unmarshall(self, raw):
		raw = raw.replace(r"\n", "\n")
		value = pickle.loads(raw)
		if self.__enhanced and isinstance(value, (list, dict)):
			value = DataFactory.from_native(value)
		return value