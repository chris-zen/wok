# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.element import DataElement

from wok.core import runstates
from wok.core.flow.model import PORT_MODE_IN, PORT_MODE_OUT

class Node(object):

	_INDENT = "  "

	def __init__(self, parent, namespace = ""):
		self.parent = parent
		self.namespace = namespace

	@property
	def name(self):
		raise Exception("Unimplemented")

	@property
	def id(self):
		if len(self.namespace) == 0:
			return self.name
		else:
			return ".".join([self.namespace, self.name])

	def __str__(self):
		return self.id

	def __repr__(self):
		sb = []
		self.repr_level(sb, 0)
		return "".join(sb)

	def repr_level(self, sb, level):
		sb.extend([self._INDENT * level,
				self.__class__.__name__, " ", self.name,
				" [", self.namespace, "]\n"])
		return level + 1

class ModelNode(Node):

	def __init__(self, parent, model, namespace = ""):
		Node.__init__(self, parent, namespace)
		self.model = model

	@property
	def name(self):
		return self.model.name

class BaseModuleNode(ModelNode):

	def __init__(self, instance, parent, model, namespace = ""):
		ModelNode.__init__(self, parent, model, namespace)

		self.instance = instance

		self.state = runstates.READY

		self.priority = None
		self.priority_factor = None

		# set of modules that should finish before it can start
		self.depends = set()

		# set of modules it is waiting for
		self.waiting = set()

		# set of modules to notify it has finished
		self.notify = set()

		self.in_ports = []
		self.in_port_map = {}

		self.out_ports = []
		self.out_port_map = {}

	def set_in_ports(self, in_ports):
		self.in_ports = in_ports
		for port in in_ports:
			self.in_port_map[port.name] = port

	def get_in_port(self, name):
		if name in self.in_port_map:
			return self.in_port_map[name]
		return None

	def set_out_ports(self, out_ports):
		self.out_ports = out_ports
		for port in out_ports:
			self.out_port_map[port.name] = port

	def get_out_port(self, name):
		if name in self.out_port_map:
			return self.out_port_map[name]
		return None

	@property
	def enabled(self):
		return self.model.enabled

	@property
	def serializer(self):
		if self.model.serializer is not None:
			return self.model.serializer

		if self.parent is not None:
			return self.parent.serializer

		return None

	@property
	def maxpar(self):
		if self.model.maxpar is not None:
			return self.model.maxpar
		elif self.parent is not None:
			return self.parent.maxpar
		return 0

	@property
	def wsize(self):
		if self.model.wsize is not None:
			return self.model.wsize
		elif self.parent is not None:
			return self.parent.wsize
		return 1

	@property
	def conf(self):
		if self.parent is None:
			conf = DataElement()
		else:
			conf = self.parent.conf

		if self.model.conf is not None:
			conf.merge(self.model.conf)

		return conf

	@property
	def resources(self):
		if self.parent is None:
			conf = DataElement()
		else:
			conf = self.parent.resources

		if self.model.resources is not None:
			conf.merge(self.model.resources)

		return conf

	@property
	def execution(self):
		return None

	@property
	def has_children(self):
		return False

	@property
	def children(self):
		return []

	def repr_level(self, sb, level):
		level = ModelNode.repr_level(self, sb, level)
		sb.extend([self._INDENT * level, "Enabled: ", str(self.enabled), "\n"])
		sb.extend([self._INDENT * level, "State: ", str(self.state), "\n"])
		if self.priority is not None:
			sb.extend([self._INDENT * level, "Priority: ", str(self.priority), "\n"])
		if self.priority_factor is not None:
			sb.extend([self._INDENT * level, "Priority factor: ", str(self.priority_factor), "\n"])
		if self.depends is not None and len(self.depends) > 0:
			sb.extend([self._INDENT * level, "Depends: ", ", ".join([m.id for m in self.depends]), "\n"])
		if self.waiting is not None and len(self.waiting) > 0:
			sb.extend([self._INDENT * level, "Waiting: ", ", ".join([m.id for m in self.waiting]), "\n"])
		if self.notify is not None and len(self.notify) > 0:
			sb.extend([self._INDENT * level, "Notify: ", ", ".join([m.id for m in self.notify]), "\n"])
		if self.model.serializer is not None:
			sb.extend([self._INDENT * level, "Serializer: ", self.model.serializer, "\n"])
		if self.model.conf is not None:
			sb.extend([self._INDENT * level, "Conf: "])
			self.model.conf.repr_level(sb, level)
			sb.append("\n")
		for p in self.in_ports:
			p.repr_level(sb, level)
		for p in self.out_ports:
			p.repr_level(sb, level)
		for m in self.modules:
			m.repr_level(sb, level)
		return level

class FlowNode(BaseModuleNode):
	def __init__(self, instance, parent, model, namespace = ""):
		BaseModuleNode.__init__(self, instance, parent, model, namespace)

		self.modules = []

	@property
	def maxpar(self):
		if self.model.maxpar is not None:
			return self.model.maxpar
		elif self.parent is not None:
			return self.parent.maxpar
		return self.instance.default_maxpar

	@property
	def wsize(self):
		if self.model.wsize is not None:
			return self.model.wsize
		elif self.parent is not None:
			return self.parent.wsize
		return self.instance.default_wsize

	@property
	def execution(self):
		return None

	@property
	def is_leaf_module(self):
		return False

	@property
	def has_children(self):
		return len(self.modules) > 0

	@property
	def children(self):
		return self.modules

	@property
	def flow_path(self):
		return self.model.path

class LeafModuleNode(BaseModuleNode):
	def __init__(self, instance, parent, model, namespace = ""):
		BaseModuleNode.__init__(self, instance, parent, model, namespace)

		self.tasks = []

	@property
	def execution(self):
		return self.model.execution

	@property
	def is_leaf_module(self):
		return True

	@property
	def modules(self):
		return []

	@property
	def has_children(self):
		return len(self.tasks) > 0

	@property
	def children(self):
		return self.tasks

	@property
	def flow_path(self):
		return self.parent.flow_path

	def repr_level(self, sb, level):
		level = BaseModuleNode.repr_level(self, sb, level)
		sb.extend([self._INDENT * level, "Tasks: ", str(len(self.tasks)), "\n"])
		level += 1
		tasks_by_state = {}
		for t in self.tasks:
			if t.state not in tasks_by_state:
				tasks_by_state[t.state] = 1
			else:
				tasks_by_state[t.state] += 1
		for state in sorted(tasks_by_state, key=lambda s: s.id):
			sb.extend([self._INDENT * level, str(state), ": ", str(tasks_by_state[state]), "\n"])
		return level - 1

class TaskNode(Node):
	def __init__(self, parent, index):
		Node.__init__(self, parent, namespace = "")

		self.index = index

		self.state = runstates.READY

		self.in_port_data = []
		self.out_port_data = []

		self.job_result = None

	@property
	def instance(self):
		return self.parent.instance

	@property
	def name(self):
		return "{}-{:04}".format(self.parent.id, self.index)

	@property
	def id(self):
		return "{}-{}".format(self.instance.name, self.name)

	@property
	def priority(self):
		return self.parent.priority + (self.index / self.parent.priority_factor * 10.0)

	@property
	def conf(self):
		return self.parent.conf

class PortNode(ModelNode):
	def __init__(self, parent, model, namespace = ""):
		ModelNode.__init__(self, parent, model, namespace)

		self.data = None

	@property
	def mode(self):
		return self.model.mode

	@property
	def serializer(self):
		if self.model.serializer is not None:
			return self.model.serializer
		if self.parent is not None:
			return self.parent.serializer
		return None

	@property
	def wsize(self):
		return self.parent.wsize

	def __str__(self):
		return self.id

	def repr_level(self, sb, level):
		level = ModelNode.repr_level(self, sb, level)
		if self.mode == PORT_MODE_IN:
			mode = "In"
		elif self.mode == PORT_MODE_OUT:
			mode = "Out"
		else:
			mode = "Unknown"
		sb.extend([self._INDENT * level, "Mode: ", mode, "\n"])
		if self.model.serializer is not None:
			sb.extend([self._INDENT * level, "Serializer: ", self.model.serializer, "\n"])
		if self.data is not None:
			sb.extend([self._INDENT * level, "Data: ", repr(self.data), "\n"])
		return level
