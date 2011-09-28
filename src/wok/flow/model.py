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

PORT_TYPE_IN = 1
PORT_TYPE_OUT = 2

_INDENT = "\t"

class Flow(object):
	def __init__(self, name, title = "", serializer = None, in_ports = None, out_ports = None, modules = None):
		self.name = name
		self.title = title
		self.serializer = None
		
		if in_ports is None:
			self.in_ports = []
			self.in_port_map = {}
		else:
			self.in_ports = in_ports
			for p in in_ports:
				self.in_port_map[p.name] = p

		if out_ports is None:
			self.out_ports = []
			self.out_port_map = {}
		else:
			self.out_ports = out_ports
			for p in out_ports:
				self.out_port_map[p.name] = p
		
		if modules is None:
			self.modules = []
			self.module_map = {}
		else:
			self.modules = modules
			for p in modules:
				self.module_map[p.name] = p

	def add_in_port(self, port):
		self.in_ports += [port]
		self.in_port_map[port.name] = port
		
	def in_port(self, name):
		return self.in_port_map[name]
	
	def add_out_port(self, port):
		self.out_ports += [port]
		self.out_port_map[port.name] = port
		
	def out_port(self, name):
		return self.out_port_map[name]
	
	def add_module(self, mod):
		self.modules += [mod]
		self.module_map[mod.name] = mod
		
	def module(self, name):
		return self.module_map[name]
		
	def __repr__(self):
		sb = ["Flow ", self.name, ":\n"]
		sb += ["\ttitle: ", self.title, "\n"]
		if self.serializer is not None:
			sb += ["\tserializer: ", self.serializer, "\n"]
		for p in self.in_ports:
			p.repr_level(sb, 1)
		for p in self.out_ports:
			p.repr_level(sb, 1)
		for m in self.modules:
			m.repr_level(sb, 1)
			
		return "".join(sb)
			
class Port(object):
	def __init__(self, name, ptype, link = None, wsize = 0, serializer = None):
		self.name = name
		self.ptype = ptype
		if link is None:
			self.link = []
		else:
			self.link = link
		self.wsize = wsize
		self.serializer = serializer
	
	def is_input(self):
		return self._ptype == PORT_TYPE_IN
		
	def is_output(self):
		return self._ptype == PORT_TYPE_OUT

	def repr_level(self, sb, level):
		if self.ptype == PORT_TYPE_IN:
			ptype = "In"
		else:
			ptype = "Out"
		sb += [_INDENT * level]
		sb += [ptype," ", self.name, ":\n"]
		level += 1
		if self.link is not None and len(self.link) > 0:
			sb += [_INDENT * level]
			sb += ["link: ", ", ".join(self.link), "\n"]
		if self.wsize > 1:
			sb += [_INDENT * level]
			sb += ["wsize: {0}\n".format(self.wsize)]
		sb += [_INDENT * level]
		if self.serializer is not None:
			sb += ["serializer: ", self.serializer, "\n"]
		return sb

	def __repr__(self):
		return "".join(self.repr_level([], 0))
							
class Module(object):
	def __init__(self, name, maxpar = 0, wsize = 0, priority = 0, enabled = True, depends = None, serializer = None, in_ports = None, out_ports = None, execution = None):
		self.name = name
		self.maxpar = maxpar
		self.wsize = wsize
		self.priority = priority
		self.enabled = enabled

		if depends is None:
			self.depends = []
		else:
			self.depends = depends

		self.serializer = serializer

		if in_ports is None:
			self.in_ports = []
			self.in_port_map = {}
		else:
			self.in_ports = in_ports
			for p in in_ports:
				self.in_port_map[p.name] = p

		if out_ports is None:
			self.out_ports = []
			self.out_port_map = {}
		else:
			self.out_ports = out_ports
			for p in out_ports:
				self.out_port_map[p.name] = p

		self.conf = None
		self.execution = execution

	def add_in_port(self, port):
		self.in_ports += [port]
		self.in_port_map[port.name] = port
		
	def in_port(self, name):
		return self.in_port_map[name]
	
	def add_out_port(self, port):
		self.out_ports += [port]
		self.out_port_map[port.name] = port
		
	def out_port(self, name):
		return self.out_port_map[name]
	
	def repr_level(self, sb, level):
		sb += [_INDENT * level]
		sb += ["Module %s:\n" % (self.name)]
		level += 1
		if not self.enabled:
			sb += [_INDENT * level, "Enabled: False\n"]
		if self.depends is not None and len(self.depends) > 0:
			sb += [_INDENT * level, "Depends: %s\n" % ", ".join(self.depends)]
		if self.serializer is not None:
			sb += [_INDENT * level, "Serializer: ", serializer, "\n"]
		for p in self.in_ports:
			p.repr_level(sb, level)
		for p in self.out_ports:
			p.repr_level(sb, level)
		if self.conf is not None:
			sb += [_INDENT * level]
			sb += ["Conf: "]
			self.conf._repr_level(sb, level)
			sb += ["\n"]
		if self.execution is not None:
			self.execution.repr_level(sb, level)
		sb += ["\n"]
		return sb

	def __repr__(self):
		return "".join(self.repr_level([], 0))
				
class Exec(object):
	def __init__(self, launcher = None, conf = None):
		self.launcher = launcher
		self.conf = conf
	
	def fill_element(self, e):
		if self.launcher:
			e["launcher"] = self.launcher
		if self.conf:
			e["conf"] = self.conf
		return e
		
	def repr_level(self, sb, level):
		sb += [_INDENT * level]
		sb += ["Exec %s: " % (self.launcher)]
		if self.conf is not None:
			self.conf._repr_level(sb, level)
			sb += ["\n"]
		return sb

	def __repr__(self):
		return "".join(self.repr_level([], 0))
