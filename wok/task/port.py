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

PORT_MODE_IN = "in"
PORT_MODE_OUT = "out"

def create_port(mode, conf, storage):
	if "port.name" not in conf:
		raise Exception("Port missing name: %s" % repr(conf))

	name = str(conf["port.name"])

	data = storage.create_port_data_from_conf(conf)

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

	def open(self):
		self._reader = self.data.reader()

	def size(self):
		return self._reader.size()
		
	def __iter__(self):
		if self._reader is None:
			self.open()

		return iter(self._reader)

	def receive(self, size = 1):
		if self._reader is None:
			self.open()
			
		return self._reader.read(size)

	def receive_all(self):
		size = self.size()
		data = self.receive(size)
		if data is None:
			data = []
		elif isinstance(data, list):
			return data
		else:
			return [data]

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

	def open(self):
		self._writer = self.data.writer()
		
	def send(self, data):
		if self._writer is None:
			self.open()

		self._writer.write(data)

	def close(self):
		if self._writer is not None:
			self._writer.close()
			self._writer = None

