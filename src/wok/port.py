from wok.portio.factory import PortDataFactory

class PortFactory(object):
	@staticmethod
	def create_port(name, conf):
		mf = conf.missing_fields(["mode", "data"])
		if len(mf) > 0:
			raise Exception("Port '%s' missing configuration: [%s]" % (name, ",".join(mf)))
		
		mode = conf["mode"]
		data = PortDataFactory.create_port_data(conf["data"])
		
		if mode == "in":
			return InPort(name, data)
		elif mode == "out":
			return OutPort(name, data)
		else:
			raise Exception("Unknown port mode: %s" % mode)

class Port(object):
	def __init__(self, name, data):
		self.name = name
		self.data = data
		
	def mode(self):
		raise Exception("Unsupported method")
		
class InPort(Port):
	def __init__(self, name, data):
		Port.__init__(self, name, data)
		
		self._reader = self.data.reader()

	def mode(self):
		return "in"

	def _open(self):
		self._reader = self.data.reader()

	def size(self):
		return self._reader.size()
		
	def __iter__(self):
		if self._reader is None:
			self._open()

		return iter(self._reader)

	def read(self, size = 1):
		if self._reader is None:
			self._open()
			
		return self._reader.read(size)

	def close(self):
		if self._reader is not None:
			self._reader.close()
			self._reader = None

class OutPort(Port):
	def __init__(self, name, data):
		Port.__init__(self, name, data)
		
		self._writer = self.data.writer()

	def mode(self):
		return "out"

	def _open(self):
		self._writer = self.data.writer()
		
	def write(self, data):
		if self._writer is None:
			self._open()

		self._writer.write(data)

	def close(self):
		if self._writer is not None:
			self._writer.close()
			self._writer = None

