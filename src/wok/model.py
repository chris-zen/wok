# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

PORT_TYPE_IN = 1
PORT_TYPE_OUT = 2

_INDENT = "\t"

class Flow(object):
	def __init__(self, name, title = "", in_ports = None, out_ports = None, modules = None):
		self.name = name
		self.title = title
		
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
		sb = ["Flow %s:\n" % self.name]
		sb += ["\ttitle: %s\n" % self.title]
		for p in self.in_ports:
			p.repr_level(sb, 1)
		for p in self.out_ports:
			p.repr_level(sb, 1)
		for m in self.modules:
			m.repr_level(sb, 1)
			
		return "".join(sb)
			
class Port(object):
	def __init__(self, name, ptype, link = None, wsize = 0):
		self.name = name
		self.ptype = ptype
		if link is None:
			self.link = []
		else:
			self.link = link
		self.wsize = wsize
	
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
		sb += ["%s %s:\n" % (ptype, self.name)]
		level += 1
		if self.link is not None and len(self.link) > 0:
			sb += [_INDENT * level]
			sb += ["link: %s\n" % ", ".join(self.link)]
		if self.wsize > 1:
			sb += [_INDENT * level]
			sb += ["wsize: %i\n" % self.wsize]
		return sb

	def __repr__(self):
		return "".join(self.repr_level([], 0))
							
class Module(object):
	def __init__(self, name, maxpar = 0, priority = 0, enabled = True, depends = None, in_ports = None, out_ports = None, execution = None):
		self.name = name
		self.maxpar = maxpar
		self.priority = priority
		self.enabled = enabled

		if depends is None:
			self.depends = []
		else:
			self.depends = depends

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
