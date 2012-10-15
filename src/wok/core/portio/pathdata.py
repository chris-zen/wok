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
import struct

from wok.core.portio import PortData, DataReader, DataWriter

class PathData(PortData):

	TYPE_NAME = "path_data"

	def __init__(self, serializer = None, path = None, partition = -1,
					start = 0, size = -1, conf = None, port_desc = None,
					factory = None):

		PortData.__init__(self, serializer, conf, port_desc, factory)

		if conf is not None:
			self._path = conf.get("path", path)
			self._partition = conf.get("partition", partition, dtype=int)
			self._start = conf.get("start", start, dtype=int)
			self._size = conf.get("size", size, dtype=int)
		else:
			self._path = path
			self._partition = partition
			self._start = start
			self._size = size

		self._last_partition = 0

	def fill_element(self, e):
		PortData.fill_element(self, e)
		e["type"] = self.TYPE_NAME
		e["path"] = self._path
		e["partition"] = self._partition
		e["start"] = self._start
		e["size"] = self._size
		return e

	def reset(self):
		self._last_partition = 0

	def _partition_size(self, partition):
		path = os.path.join(self._path, "%06d.index" % partition)
		if os.path.exists(path):
			return os.path.getsize(path) / 8
		else:
			return 0

	def get_slice(self, start = None, size = None):
		if start is None and size is None:
			return PathData(self._serializer, self._path, self._partition,
							self._start, self._size, port_desc = self.port_desc)

		partition = 0

		ps = self._partition_size(partition)

		if start is None:
			start = 0
		else:
			#print "p=%d, ps=%d, start=%d" % (partition, ps, start)
			while start >= ps and start != 0:
				partition += 1
				start -= ps
				ps = self._partition_size(partition)
				#print "p=%d, ps=%d, start=%d" % (partition, ps, start)

		if size is None:
			size = 0

		return PathData(self._serializer, self._path, partition,
						start, size, port_desc = self.port_desc)

	def get_partition(self, partition = None):
		if partition is None:
			partition = self._last_partition
			self._last_partition += 1

		return PathData(self._serializer, self._path, partition = partition,
						port_desc = self.port_desc)
	
	def size(self):
		if not os.path.exists(self._path):
			self._size = 0
		elif self._partition == -1:
			self._size = 0
			if os.path.exists(self._path):
				for f in os.listdir(self._path):
					if f.endswith(".index"):
						path = os.path.join(self._path, f)
						self._size += os.path.getsize(path) / 8
		else:
			path = os.path.join(self._path, "%06d.index" % self._partition)
			if os.path.exists(path):
				self._size = (os.path.getsize(path) / 8) - self._start
			else:
				self._size = 0
		return self._size

	def reader(self):
		if self._partition == -1 and self._size == -1:
			raise Exception("A reader can not be created without knowing the partition and/or size")
	
		return PartitionDataReader(self._serializer, self._path, self._partition, self._start, self._size)
	
	def writer(self):
		if self._partition == -1:
			raise Exception("A writer can not be created without knowing the partition")

		return PartitionDataWriter(self._serializer, self._path, self._partition)
		
	def __repr__(self):
		sb = [self._path]
		if self._partition != -1 or self._start != 0 or self._size != -1:
			sb += [" "]
			if self._partition != -1:
				sb + [str(self._partition), "."]
			sb += [str(self._start)]
			if self._size != -1:
				sb += [":", str(self._start + self._size - 1)]
		return "".join(sb)

class PartitionDataReader(DataReader):
	def __init__(self, serializer, path, partition, start, size):
		DataReader.__init__(self, serializer)

		self._path = path
		self._partition = partition
		self._start = start
		self._size = size
	
		self._index_path = None
		self._data_path = None
		
		self._index_f = None
		self._data_f = None

	def open(self):
		if self._data_f is not None:
			self.close()

		self._index_path = os.path.join(self._path, "%06d.index" % self._partition)
		self._data_path = os.path.join(self._path, "%06d.data" % self._partition)
		
		self._index_f = open(self._index_path, "rb")
		self._data_f = open(self._data_path, "r")
		
		self._index_f.seek(self._start * 8)
	
	def close(self):
		if self._index_f is not None:
			self._index_f.close()
			self._index_f = None
		if self._data_f is not None:
			self._data_f.close()
			self._data_f = None

	def is_opened(self):
		return self._data_f is not None

	def next(self):
		if self._size == 0:
			raise StopIteration()

		if self._data_f is None:
			self.open()

		d = self._index_f.read(8)
		if len(d) < 8:
			self._partition += 1
			self._start = 0

			self.open()
			
			d = self._index_f.read(8)
			
			if len(d) < 8:
				raise StopIteration()

		pos = struct.unpack("Q", d)[0]
		self._data_f.seek(pos)
		data = self._data_f.readline().rstrip()
		data = self._serializer.unmarshall(data)
		
		self._size -= 1

		return data
	
class PartitionDataWriter(DataWriter):
	def __init__(self, serializer, path, partition):
		DataWriter.__init__(self, serializer)

		self._path = path
		self._partition = partition

		if not os.path.exists(path):
			os.makedirs(path)
		
		self._index_path = os.path.join(path, "%06d.index" % partition)
		self._data_path = os.path.join(path, "%06d.data" % partition)

		self._index_f = None
		self._data_f = None

	def open(self):
		if self._data_f is not None:
			self.close()
		self._index_f = open(self._index_path, "wb+")
		self._data_f = open(self._data_path, "w+")
		
	def close(self):
		if self._index_f is not None:
			self._index_f.close()
			self._index_f = None
		if self._data_f is not None:
			self._data_f.close()
			self._data_f = None
		
	def write(self, data):
		if self._data_f is None:
			self.open()

		if not isinstance(data, list):
			data = [data]
		
		for d in data:
			# Update the index
			pos = self._data_f.tell()
			self._index_f.write(struct.pack("Q", pos))
		
			# Write the data
			d = self._serializer.marshall(d)
			self._data_f.write(d)
			self._data_f.write("\n")

	def __repr__(self):
		return "%s/%06d" % (self._path, self._partition)
