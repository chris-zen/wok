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

	def to_element(self, e = None):
		if e is None:
			e = DataElement()

		e["id"] = self.id
		e["name"] = self.name
		
		return e

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

		# number of tasks of each state {<state, count>}
		self._tasks_count_by_state = {}

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
	def tasks_count_by_state(self):
		return self._tasks_count_by_state

	@property
	def has_children(self):
		return False

	@property
	def children(self):
		return []

	def to_element(self, e = None):
		e = ModelNode.to_element(self, e)
		e["state"] = str(self.state)
		e["state_msg"] = "" #TODO
		e["priority"] = self.priority
		e["depends"] = [m.id for m in self.depends]
		e["enabled"] = self.enabled
		e["serializer"] = self.serializer
		e["maxpar"] = self.maxpar
		e["wsize"] = self.wsize
		e["conf"] = self.conf
		e["resources"] = self.resources
		e.create_element("tasks_count", self._tasks_count_by_state)

		ports = e.create_element("ports")
		in_ports = ports.create_list("in")
		for port in self.in_ports:
			in_ports.append(port.to_element())
		out_ports = ports.create_list("out")
		for port in self.out_ports:
			out_ports.append(port.to_element())		
		return e

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

		# number of modules of each state {<state, count>}
		self._modules_count_by_state = {}

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

	@property
	def modules_count_by_state(self):
		return self.__modules_count_by_state

	def update_tasks_count_by_state(self):
		count = {}
		for module in self.modules:
			mcount = module.update_tasks_count_by_state()
			for state, cnt in mcount.items():
				s = str(state)
				if s not in count:
					count[s] = cnt
				else:
					count[s] += cnt
		self._tasks_count_by_state = count
		return count

	def update_modules_count_by_state(self):
		count = {}
		for module in self.modules:
			mcount = module.update_modules_count_by_state()
			for state, cnt in mcount.items():
				s = str(state)
				if s not in count:
					count[s] = cnt
				else:
					count[s] += cnt
		self._modules_count_by_state = count
		return count

	def to_element(self, e = None):
		e = BaseModuleNode.to_element(self, e)
		mlist = e.create_list("modules")
		for module in self.modules:
			mlist.append(module.to_element())

		e.create_element("modules_count", self._modules_count_by_state)
		return e

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

	def update_tasks_count_by_state(self):
		count = {}
		for task in self.tasks:
			s = str(task.state)
			if s not in count:
				count[s] = 1
			else:
				count[s] += 1
		self._tasks_count_by_state = count
		return count

	def update_modules_count_by_state(self):
		return { str(self.state) : 1 }
	
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
