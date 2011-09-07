# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

PORT_MODE_IN = 1
PORT_MODE_OUT = 2

class _Base(object):
	_INDENT = "  "

	def __ini__(self):
		pass

class _BaseDesc(_Base):

	def __init__(self, name, title = "", desc = "", enabled = True):
		self.name = name
		self.title = title
		self.desc = desc
		self.enabled = enabled

	def __repr__(self):
		sb = []
		self.repr_level(sb, 0)
		return "".join(sb)

	def repr_level(self, sb, level):
		sb.extend([self._INDENT * level, self.__class__.__name__, " ", self.name, "\n"])
		level += 1
		sb.extend([self._INDENT * level, "Enabled: ", str(self.enabled), "\n"])
		if self.title is not None:
			sb.extend([self._INDENT * level, "Title: ", self.title, "\n"])
		if self.desc is not None:
			sb.extend([self._INDENT * level, "Desc: ", self.desc, "\n"])
		return level

class _BasePort(_BaseDesc):
	def __init__(self, name, title = "", desc = "", enabled = True,
					serializer = None, wsize = None):
		_BaseDesc.__init__(self, name, title, desc, enabled)

		self.serializer = serializer
		self.wsize = wsize

	def repr_level(self, sb, level):
		level = _BaseDesc.repr_level(self, sb, level)
		if self.serializer is not None:
			sb.extend([self._INDENT * level, "Serializer: ", self.serializer, "\n"])
		if self.wsize is not None:
			sb.extend([self._INDENT * level, "Wsize: ", str(self.wsize), "\n"])
		return level

class _BaseModule(_BasePort):
	def __init__(self, name, title = "", desc = "", enabled = True,
					serializer = None, wsize = None,
					maxpar = None, conf = None, in_ports = None, out_ports = None):
		_BasePort.__init__(self, name, title, desc, enabled, serializer, wsize)

		self.maxpar = maxpar
		self.conf = conf

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

	def add_in_port(self, port):
		self.in_ports += [port]
		self.in_port_map[port.name] = port

	def in_port(self, name):
		return self.in_port_map.get(name)

	def add_out_port(self, port):
		self.out_ports += [port]
		self.out_port_map[port.name] = port

	def out_port(self, name):
		return self.out_port_map.get(name)

	def repr_level(self, sb, level):
		level = _BasePort.repr_level(self, sb, level)
		if self.maxpar is not None:
			sb.extend([self._INDENT * level, "Maxpar: ", str(self.maxpar), "\n"])
		if self.conf is not None:
			sb.extend([self._INDENT * level, "Conf: "])
			self.conf.repr_level(sb, level)
			sb.append("\n")
		for p in self.in_ports:
			p.repr_level(sb, level)
		for p in self.out_ports:
			p.repr_level(sb, level)
		return level

class Flow(_BaseModule):
	def __init__(self, name, title = "", desc = "", enabled = True,
					serializer = None, wsize = None,
					maxpar = None, conf = None, in_ports = None, out_ports = None,
					path = None, library = None, modules = None):
		_BaseModule.__init__(self, name, title, desc, enabled, serializer, wsize, maxpar, conf, in_ports, out_ports)

		self.path = path

		self.library = library

		if modules is None:
			self.modules = []
			self.module_map = {}
		else:
			self.modules = modules
			for p in modules:
				self.module_map[p.name] = p
	
	def add_module(self, mod):
		self.modules += [mod]
		self.module_map[mod.name] = mod
		
	def module(self, name):
		return self.module_map[name]
		
	def repr_level(self, sb, level):
		level = _BaseModule.repr_level(self, sb, level)
		if self.path is not None:
			sb.extend([self._INDENT * level, "Path: ", self.path, "\n"])
		if self.library is not None:
			sb.extend([self._INDENT * level, "Library: ", self.library, "\n"])
		if self.version is not None:
			sb.extend([self._INDENT * level, "Version: ", self.version, "\n"])
		for m in self.modules:
			m.repr_level(sb, level)
		return level

class Module(_BaseModule):
	def __init__(self, name, title = "", desc = "", enabled = True,
					maxpar = None, wsize = None, serializer = None,
					conf = None, in_ports = None, out_ports = None,
					priority = None, depends = None, flow_ref = None, execution = None):
		_BaseModule.__init__(self, name, title, desc, enabled, serializer, wsize, maxpar, conf, in_ports, out_ports)

		self.priority = priority
		
		if depends is None:
			self.depends = []
		else:
			self.depends = depends

		self.flow_ref = flow_ref
		
		self.execution = execution

	def repr_level(self, sb, level):
		level = _BaseModule.repr_level(self, sb, level)
		if self.priority is not None:
			sb.extend([self._INDENT * level, "Priority: ", self.priority, "\n"])
		if self.depends is not None and len(self.depends) > 0:
			sb.extend([self._INDENT * level, "Depends: %s\n" % ", ".join(self.depends)])
		if self.flow_ref is not None:
			self.flow_ref.repr_level(sb, level)
		if self.execution is not None:
			self.execution.repr_level(sb, level)
		sb.extend(["\n"])
		return level

class Port(_BasePort):
	def __init__(self, name, title = "", desc = "", enabled = True,
					serializer = None, wsize = None,
					mode = None, link = None):
		_BasePort.__init__(self, name, title, desc, enabled, serializer, wsize)

		self.mode = mode
		if link is None:
			self.link = []
		else:
			self.link = link

	def is_input(self):
		return self._ptype == PORT_MODE_IN

	def is_output(self):
		return self._ptype == PORT_MODE_OUT

	def repr_level(self, sb, level):
		level = _BasePort.repr_level(self, sb, level)
		if self.mode == PORT_MODE_IN:
			mode = "In"
		elif self.mode == PORT_MODE_OUT:
			mode = "Out"
		else:
			mode = "Unknown"
		sb.extend([self._INDENT * level, "Mode: ", mode, "\n"])
		if self.link is not None and len(self.link) > 0:
			sb.extend([self._INDENT * level, "Links: ", ", ".join(self.link), "\n"])
		return level

class Exec(_Base):
	def __init__(self, launcher = None, conf = None):
		self.mode = launcher
		self.conf = conf
	
	def fill_element(self, e):
		if self.mode:
			e["mode"] = self.mode
		if self.conf:
			e["conf"] = self.conf
		return e
		
	def repr_level(self, sb, level):
		sb.extend([self._INDENT * level, "Exec "])
		if self.mode is not None:
			sb.append(self.mode)
		if self.conf is not None:
			sb.append(" ")
			self.conf.repr_level(sb, level)
		return level

class FlowRef(_Base):
	def __init__(self, canonical_name = None, version = None):
		_Base.__init__(self)

		self.canonical_name = canonical_name
		self.version = version

	@property
	def uri(self):
		if self.version is not None:
			return "{}/{}".format(self.canonical_name, self.version)
		else:
			return self.canonical_name

	def repr_level(self, sb, level):
		sb.extend([self._INDENT * level, "FlowRef ", self.uri])
		return level