# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.portio import PortData

TYPE_MULTI_DATA = "multi_data"

class MultiData(PortData):
	def __init__(self, sources, start = 0, size = -1, conf = None):
		PortData.__init__(self, None, conf)

		if conf is not None:
			self._sources = []
			from wok.portio.factory import PortDataFactory
			for sconf in conf["sources"]:
				self._source += [PortDataFactory.create_port_data(sconf)]
			self._start = conf.get("start", start, dtype=int)
			self._size = conf.get("size", size, dtype=int)
		else:
			self._sources = sources
			self._start = start
			self._size = size

	def size(self):
		return sum([src.size() for src in self._sources])

	def fill_element(self, e):
		PortData.fill_element(self, e)
		e["type"] = TYPE_MULTI_DATA
		e["start"] = self._start
		e["size"] = self._size
		l = e.create_list()
		for src in self._sources:
			pe = e.create_element()
			l += [src.fill_element(pe)]
		e["sources"] = l
		return e
	
	def get_slice(self, start = None, size = None):
		if start is None:
			start = self._start
		if size is None:
			size = self._size

		return MultiData(self._sources, start, size)

	def reader(self):
		raise Exception("Unimplemented")

	def __repr__(self):
		sb = ["[", ", ".join([str(x) for x in self._sources]), "]"]
		if self._start != 0 and self._size != -1:
			sb += [" ", str(self._start)]
			if self._size != -1:
				sb += [":", str(self._start + self._size - 1)]
		return "".join(sb)

