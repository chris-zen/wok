# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.serializer import DEFAULT_SERIALIZER_NAME
from wok.serializer import SerializerFactory

class PortData(object):
	def __init__(self, serializer = None, conf = None):
		"""Initialize the port data"""

		if conf is not None:
			self._serializer = conf.get("serializer", DEFAULT_SERIALIZER_NAME)
		else:
			if serializer is None:
				self._serializer = DEFAULT_SERIALIZER_NAME
			else:
				self._serializer = serializer

	@property
	def serializer(self):
		return self._serializer

	def fill_element(self, e):
		"""Fill the DataElement e with attributes of the port data"""

		e["serializer"] = self._serializer
		return e

	def reset(self):
		"""Reset port data state"""
		pass

	def size(self):
		"""Get the port data size"""
		raise Exception("Unimplemented")
		
	def get_slice(self, start = None, size = None):
		"""Get an slice of the port data. It is only used for input ports"""
		raise Exception("Unimplemented")

	def get_partition(self, partition):
		"""Get a partition of the port data. It is only used for output ports"""
		raise Exception("Read only port can not give partitions")
		
	def reader(self):
		"""Get a port data reader"""
		raise Exception("Port doesn't support reading")
		
	def writer(self):
		"""Get a port data writer"""
		raise Exception("Port doesn't support writing")


class DataReader(object):
	def __init__(self, serializer = None):
		if serializer:
			self._serializer = SerializerFactory.create(serializer)
		else:
			self._serializer = None

	def next(self):
		raise Exception("Unimplemented")

	def __iter__(self):
		return self

	def size(self):
		return self._size

	def read(self, size = 1):
		data = []
		if self.size() == 0:
			return None

		if not self.is_opened():
			self._open()

		try:
			while size > 0:
				data += [self.next()]
				size -= 1
		except StopIteration:
			pass

		if len(data) == 0:
			return None
		elif len(data) == 1:
			return data[0]
		else:
			return data

class DataWriter(object):
	def __init__(self, serializer):
		self._serializer = SerializerFactory.create(serializer)