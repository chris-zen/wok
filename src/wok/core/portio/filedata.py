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

import os

from wok.core.portio.base import PortData, DataReader

class FileData(PortData):

	TYPE_NAME = "file_data"

	def __init__(self, serializer = None, path = None, start = 0, size = -1,
					conf = None, port_desc = None, factory = None):

		PortData.__init__(self, serializer, conf, port_desc, factory)

		if conf is not None:
			self._path = conf.get("path", path)
			self._start = conf.get("start", start, dtype=int)
			self._size = conf.get("size", size, dtype=int)
			self._seek_pos = conf.get("seek_pos", -1, dtype=long)
		else:
			self._path = path
			self._start = start
			self._size = size
			self._seek_pos = -1

	def fill_element(self, e):
		PortData.fill_element(self, e)

		e["type"] = self.TYPE_NAME
		e["path"] = self._path
		e["start"] = self._start
		e["size"] = self._size
		if self._seek_pos >= 0:
			e["seek_pos"] = self._seek_pos
		return e

	def get_slice(self, start = None, size = None):
		if start is None:
			start = self._start
		if size is None:
			size = self._size
		return FileData(self._serializer, self._path, start, size)

	def size(self):
		if self._size == -1:
			if not os.path.exists(self._path):
				self._size = 0
			else:
				self._size = 0
				f = open(self._path, "r")
				self._size = sum([1 for _ in f])
				f.close()
		return self._size

	def reader(self):
		return FileDataReader(self._serializer, self._path, self._start, self._size, self._seek_pos)

	def __repr__(self):
		sb = [self._path]
		if self._start != 0 and self._size != -1:
			sb += [" %i" % self._start]
			if self._size != -1:
				sb += [":%i" % (self._start + self._size - 1)]
		return "".join(sb)
		
class FileDataReader(DataReader):
	def __init__(self, serializer, path, start, size, seek_pos = -1):
		DataReader.__init__(self, serializer)

		self._path = path
		self._start = start
		self._size = size
		self._seek_pos = seek_pos

		self._data_f = None

	def _open(self):
		if self._data_f is not None:
			self.close()

		self._data_f = open(self._path, "r")

		if self._seek_pos >= 0:
			self._reader.seek(self._seek_pos)
		else:
			for _ in xrange(self._start):
				self._data_f.readline()

	def close(self):
		if self._data_f is not None:
			self._data_f.close()
			self._data_f = None

	def is_opened(self):
		return self._data_f is not None

	def next(self):
		if self._size == 0:
			raise StopIteration()

		if self._data_f is None:
			self._open()

		data = self._data_f.readline().rstrip()
		data = self._serializer.unmarshall(data)

		self._size -= 1

		return data

	def __repr__(self):
		sb = [self._path]
		if self._start != 0 and self._size != -1:
			sb += [" %i" % self._start]
			if self._size != -1:
				sb += [":%i" % (self._start + self._size - 1)]
		if self._seek_pos >= 0:
			sb += [" seek = %s" % str(self._seek_pos)]
		return "".join(sb)
