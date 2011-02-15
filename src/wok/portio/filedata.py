import os

from wok.portio import PortData

TYPE_FILE_DATA = "file_data"

class FileData(PortData):
	def __init__(self, path = None, start = 0, size = -1, conf = None):
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
		e["type"] = TYPE_FILE_DATA
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
		return FileData(self._path, start, size)

	def size(self):
		if self._size == -1:
			if not os.path.exists(self._path):
				self._size = 0
			else:
				self._size = 0
				f = open(self._path, "r")
				self._size = sum([1 for line in f])
				f.close()
		return self._size

	def reader(self):
		#if self._size == -1:
		#	size = self.size()
		#else:
		#	size = self._size
		
		return FileDataReader(self._path, self._start, self._size, self._seek_pos)

	def writer(self):
		raise Exception("Unimplemented")

	def __repr__(self):
		sb = [self._path]
		if self._start != 0 and self._size != -1:
			sb += [" %i" % self._start]
			if self._size != -1:
				sb += [":%i" % (self._start + self._size - 1)]
		return "".join(sb)
		
class FileDataReader(object):
	def __init__(self, path, start, size, seek_pos = -1):
		self._path = path
		self._start = start
		self._size = size
		self._seek_pos = seek_pos

		self._reader = None

	def _open(self):
		if self._reader is not None:
			self._close()
		return open(self._path, "r")

	def _seek(self):
		if self._seek_pos >= 0:
			self._reader.seek(self._seek_pos)
		else:
			for i in xrange(self._start):
				self._reader.readline()

	def close(self):
		if self._reader is not None:
			self._reader.close()
			self._reader = None

	def __iter__(self):
		if self._reader is None:
			self._reader = self._open()

		self._seek()

		if self._size <= 0:
			return

		count = 0
		for line in self._reader:
			yield line.rstrip().replace(r"\n", "\n")

			count += 1
			if count >= self._size:
				self.close()
				return

	def __repr__(self):
		sb = [self._path]
		if self._start != 0 and self._size != -1:
			sb += [" %i" % self._start]
			if self._size != -1:
				sb += [":%i" % (self._start + self._size - 1)]
		if self._seek_pos >= 0:
			sb += [" seek = %s" % str(self._seek_pos)]
		return "".join(sb)
