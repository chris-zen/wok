import os

from wok.portio import PortData

TYPE_MULTI_DATA = "multi_data"

class MultiData(PortData):
	def __init__(self, paths, start = 0, size = -1, conf = None):
		if conf is not None:
			if "paths" in conf:
				self._paths = conf[paths].to_native()
			else:
				self._paths = []
			self._start = conf.get("start", start, dtype=int)
			self._size = conf.get("size", size, dtype=int)
		else:
			self._paths = paths
			self._start = start
			self._size = size

	def size(self):
		return sum([path.size() for path in self._paths])

	def fill_element(self, e):
		e["type"] = TYPE_MULTI_DATA
		e["paths"] = l = e.create_list()
		for path in self._paths:
			pe = e.create_element()
			l += [path.fill_element(pe)]
		return e
	
	def __iter__(self):
		raise Exception("Unimplemented")
	
	def __repr__(self):
		sb = ["[%s]" % ", ".join([str(x) for x in self._paths])]
		if self._start != 0 and self._size != -1:
			sb += [" %i" % self._start]
			if self._size != -1:
				sb += [":%i" % (self._start + self._size - 1)]
		return "".join(sb)

