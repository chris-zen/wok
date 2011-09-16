# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.portio.factory import PortDataFactory

PORT_MODE_IN = "in"
PORT_MODE_OUT = "out"

class PortFactory(object):
	@staticmethod
	def create_port(name, conf):
		mf = conf.missing_fields(["mode", "data"])
		if len(mf) > 0:
			raise Exception("Port '%s' missing configuration: [%s]" % (name, ",".join(mf)))
		
		mode = conf["mode"]
		data = PortDataFactory.create_port_data(conf["data"])
		
		if mode == PORT_MODE_IN:
			return InPort(name, data)
		elif mode == PORT_MODE_OUT:
			return OutPort(name, data)
		else:
			raise Exception("Unknown port mode: %s" % mode)

class Port(object):
	def __init__(self, name, data):
		self.name = name
		self.data = data

	@property
	def mode(self):
		raise Exception("Unsupported method")
		
class InPort(Port):
	def __init__(self, name, data):
		Port.__init__(self, name, data)
		
		self._reader = self.data.reader()

	@property
	def mode(self):
		return PORT_MODE_IN

	def _open(self):
		self._reader = self.data.reader()

	def size(self):
		return self._reader.size()
		
	def __iter__(self):
		if self._reader is None:
			self._open()

		return iter(self._reader)

	def receive(self, size = 1):
		if self._reader is None:
			self._open()
			
		return self._reader.read(size)

	# DEPRECATED, for backward compatibility
	def read(self, size = 1):
		return self.read(size)

	def receive_all(self):
		size = self.size()
		data = self.read(size)
		if data is None:
			data = []
		elif isinstance(data, list):
			return data
		else:
			return [data]

	# DEPRECATED, for backward compatibility
	def read_all(self):
		return self.receive_all()

	def close(self):
		if self._reader is not None:
			self._reader.close()
			self._reader = None

class OutPort(Port):
	def __init__(self, name, data):
		Port.__init__(self, name, data)
		
		self._writer = self.data.writer()

	@property
	def mode(self):
		return PORT_MODE_OUT

	def _open(self):
		self._writer = self.data.writer()
		
	def send(self, data):
		if self._writer is None:
			self._open()

		self._writer.write(data)

	# DEPRECATED, for backward compatibility
	def write(self, data):
		self.send(data)

	def close(self):
		if self._writer is not None:
			self._writer.close()
			self._writer = None

