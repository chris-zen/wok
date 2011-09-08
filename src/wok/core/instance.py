# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

import sys
import os.path
import math

from wok import logger
from wok.element import DataElement
from wok.core import runstates
from wok.core.nodes import *
from wok.core.storage.base import StorageContext
from wok.core.storage.factory import create_storage

from wok.core.portio.filedata import FileData
from wok.core.portio.pathdata import PathData
from wok.core.portio.multidata import MultiData

class Instance(object):

	_INDENT = "  "

	def __init__(self, engine, name, conf_builder, flow_file):
		self.engine = engine

		self.name = name
		
		self.conf = None
		self.conf_builder = conf_builder

		self.flows = []
		self.flow_file = flow_file
		self.root_flow = None

		self.root_node = None
	
	def initialize(self):
		self.conf = self.conf_builder()

		wok_conf = self.conf["wok"]
		inst_conf = wok_conf["__instance"]

		self._log = logger.get_logger(wok_conf.get("log"), self.name)

		self._work_path = inst_conf["work_path"] # TODO deprecated

		self.storage = self._create_storage(wok_conf)

		if "port_map" in wok_conf:
			self._port_data_conf = wok_conf["port_map"]
		else:
			self._port_data_conf = wok_conf.create_element()

		self.default_maxpar = wok_conf.get("defaults.maxpar", 0, dtype=int)
		self.default_wsize = wok_conf.get("defaults.wsize", 1, dtype=int)

		self.root_flow = self.engine.flow_loader.load_from_file(self.flow_file)

		# self._log.debug("\n" + repr(self.root_flow))

		# create nodes tree
		self.root_node = self._create_tree(self.root_flow, namespace = "")

		# connect ports
		self._connect_ports(self.root_node, namespace = self.root_node.name)

		# calculcate dependencies
		self._calculate_dependencies(self.root_node)

		# calculate priorities
		for m in self.root_node.modules:
			self._calculate_priorities(m)

		# TODO self._save_initial_state()

		# self._log.debug("Flow node tree:\n" + repr(self.root_node))

	@property
	def state(self):
		return self.root_node.state

	def _save_initial_state(self):
		raise Exception("Not yet implemented")

	def _load_state(self):
		raise Exception("Not yet implemented")

	@staticmethod
	def _create_storage(wok_conf):
		storage_conf = wok_conf.get("storage")
		if storage_conf is None:
			storage_conf = wok_conf.create_element()

		storage_type = storage_conf.get("type", "sfs")

		if "work_path" not in storage_conf:
			wok_work_path = wok_conf.get("work_path", os.path.join(os.getcwd(), "wok"))
			storage_conf["work_path"] = os.path.join(wok_work_path, storage_type)

		return create_storage(storage_type, StorageContext.SERVER, storage_conf)

	def _create_tree(self, flow_def, parent = None, namespace = ""):

		#self._log.debug("_create_tree({}, {}, {})".format(flow_def.name, parent, namespace))

		flow = FlowNode(instance = self, parent = parent, model = flow_def, namespace = namespace)

		if len(namespace) > 0:
			ns = ".".join([namespace, flow_def.name])
		else:
			ns = flow_def.name

		# create flow port nodes
		flow.set_in_ports(self._create_port_nodes(flow, flow_def.in_ports, ns))
		flow.set_out_ports(self._create_port_nodes(flow, flow_def.out_ports, ns))

		# create module nodes
		for mod_def in flow_def.modules:
			if mod_def.flow_ref is None:
				module = LeafModuleNode(instance = self, model = mod_def, parent = flow, namespace = ns)
				mns = ".".join([ns, module.name])

				# create module port nodes
				module.set_in_ports(self._create_port_nodes(module, mod_def.in_ports, mns))
				module.set_out_ports(self._create_port_nodes(module, mod_def.out_ports, mns))
			else:
				sub_flow_def = self.engine.flow_loader.load_from_ref(mod_def.flow_ref)
				self._override_module(sub_flow_def, mod_def)
				module = self._create_tree(sub_flow_def, parent = flow, namespace = ns)
				# link module ports according to mod_def
				for port_def in mod_def.in_ports:
					port = module.get_in_port(port_def.name)
					if port is None:
						raise Exception("The port {} is not defined in the flow {}".format(port_def.name, mod_def.flow_ref.uri))
					self._override_port(port.model, port_def)
				for port_def in mod_def.out_ports:
					port = module.get_out_port(port_def.name)
					if port is None:
						raise Exception("The port {} is not defined in the flow {}".format(port_def.name, mod_def.flow_ref.uri))
					if port_def.serializer is not None:
						port.model.serializer = port_def.serializer
					port.model.link = port_def.link

			flow.modules += [module]

		return flow

	@staticmethod
	def _create_port_nodes(module, port_defs, namespace):
		port_names = set()
		ports = []
		for port_def in port_defs:
			if port_def.name in port_names:
				sb = ["Duplicated port name '{}'".format(port_def.name)]
				if len(namespace) > 0:
					sb += [" at '{}'".format(namespace)]
				raise Exception("".join(sb))

			port_names.add(port_def.name)

			port = PortNode(parent = module, model = port_def, namespace = namespace)
			ports += [port]

		return ports

	def _connect_ports(self, module, namespace):

		#self._log.debug("_connect_ports({}, {})".format(module.name, namespace))
		
		if len(namespace) > 0:
			gid_func = lambda name: ".".join([namespace, name])
			mid_func = lambda mname, pname: ".".join([namespace, mname, pname])
		else:
			gid_func = lambda name: name
			mid_func = lambda mname, pname: ".".join([mname, pname])

		ports = []
		port_map = {}

		# root module ports
		for port in module.in_ports:
			pid = gid_func(port.name)
			ports += [(pid, port)]
			port_map[pid] = port

		for port in module.out_ports:
			pid = gid_func(port.name)
			ports += [(pid, port)]
			port_map[pid] = port

		# cildren modules ports
		for mod in module.modules:
			for port in mod.in_ports:
				pid = mid_func(mod.name, port.name)
				ports += [(pid, port)]
				port_map[pid] = port
			for port in mod.out_ports:
				pid = mid_func(mod.name, port.name)
				ports += [(pid, port)]
				port_map[pid] = port

		#self._log.debug("ports:\n" + "\n".join(["\t" + p[0] for p in ports]))

		# first the ports which are source for others
		for port_id, port in ports:
			# if the port is already connected skip it
			if port.data is not None:
				continue

			port_def = port.model
			if port_id in self._port_data_conf: # attached through user configuration
				port_def.link = [] # override flow specified connections
				port_data_conf = self._port_data_conf[port_id]
				if isinstance(port_data_conf, DataElement):
					raise Exception("Configurable attached port unimplemented")
				else: # By default we expect a file/dir path
					path = str(port_data_conf)
					if not os.path.exists(path):
						raise Exception("Port {}: File not found: {}".format(port_id, path))

					if os.path.isdir(path):
						port.data = PathData(port.serializer, path)
					elif os.path.isfile(path):
						port.data = FileData(port.serializer, path)
					else:
						raise Exception("Port {}: Unexpected path type: {}".format(port_id, path))

			elif len(port_def.link) == 0: # link not defined (they are source ports)
				rel_path = port_id.replace(".", "/")
				path = os.path.join(self._work_path, "ports", rel_path)
				if not os.path.exists(path):
					os.makedirs(path)
				port.data = PathData(port.serializer, path)
				#self._log.debug(">>> {} -> [{}] {}".format(port.parent.id, id(port.data), port.data))

		# then the ports that link to source ports
		for port_id, port in ports:
			# if the port is already connected skip it
			if port.data is not None:
				continue
	
			port_def = port.model
			if len(port_def.link) > 0:
				data = []
				for link in port_def.link:
					link = gid_func(link)
					if link not in port_map:
						#self._log.debug("port_map:\n" + "\n".join(["{}: {}".format(p[0], repr(port_map[p[0]])) for p in ports]))
						raise Exception("Port {} references a non-existent port: {}".format(port_id, link))

					link_port = port_map[link]

					if port.serializer is not None and port.serializer != link_port.serializer:
						raise Exception("Unmatching serializer found while linking port '{}' [{}] with '{}' [{}]".format(port.id, port.serializer, link_port.id, link_port.serializer))

					data += [link_port.data]

				if len(data) == 1:
					port.data = data[0]
				else:
					port.data = MultiData(data)

		# check that there are no ports without data
		for port_id, port in ports:
			if port.data is None:
				raise Exception("Unconnected port: {}".format(port_id))

		#self._log.debug("port_map:\n" + "\n".join(["{}: {}".format(p[0], repr(port_map[p[0]])) for p in ports]))

		# connect children modules ports
		for mod in module.modules:
			if len(mod.modules) > 0:
				self._connect_ports(mod, gid_func(mod.name))

	@staticmethod
	def _override_module(ovr_mod, src_mod):
		ovr_mod.name = src_mod.name
		if src_mod.title is not None:
			ovr_mod.title = src_mod.title
		if src_mod.desc is not None:
			ovr_mod.desc = src_mod.desc
		if src_mod.enabled is not None:
			ovr_mod.enabled = src_mod.enabled
		if src_mod.serializer is not None:
			ovr_mod.serializer = mode_def.serializer
		if src_mod.wsize is not None:
			ovr_mod.wsize = mode_def.wsize
		if src_mod.conf is not None:
			if ovr_mod.conf is None:
				ovr_mod.conf = DataElement()
			ovr_mod.conf.merge(mode_def.conf)

		ovr_mod.priority = src_mod.priority
		ovr_mod.depends = src_mod.depends
		ovr_mod.flow_ref = src_mod.flow_ref

	@staticmethod
	def _override_port(ovr_port, src_port):
		if src_port.title is not None:
			ovr_port.title = src_port.title
		if src_port.desc is not None:
			ovr_port.desc = src_port.desc
		if src_port.enabled is not None:
			ovr_port.enabled = src_port.enabled
		if src_port.serializer is not None:
			ovr_port.serializer = src_port.serializer
		if src_port.wsize is not None:
			ovr_port.wsize = src_port.wsize
		ovr_port.link = src_port.link

	def _calculate_dependencies(self, module):
		mod_source_map = {} # module <-> sources required by the module
		mod_name_map = {} # module id <-> module
		source_map = {} # source <-> modules that provide the source

		self._prepare_dependency_map(module, mod_source_map, mod_name_map, source_map)

		#self._log.debug("mod_source_map:\n" + "\n".join(sorted(["{} --> {}".format(k.id, ", ".join(["[{}] {}".format(id(x), x) for x in v])) for k,v in mod_source_map.items()])))
		#self._log.debug("source_map:\n" + "\n".join(sorted(["{} <-- {}".format("[{}] {}".format(id(k), k), ", ".join([x.id for x in v])) for k,v in source_map.items()])))
		
		self._apply_dependencies(module, mod_source_map, mod_name_map, source_map)

	def _prepare_dependency_map(self, module, mod_source_map, mod_name_map, source_map):
		mod_name_map[module.id] = module
		for port in module.in_ports:
			if isinstance(port.data, MultiData):
				data = set(port.data.sources)
			else:
				data = set([port.data])
			if module not in mod_source_map:
				mod_source_map[module] = data
			else:
				mod_source_map[module].update(data)
		for port in module.out_ports:
			if port.data not in source_map:
				source_map[port.data] = set([module])
			else:
				source_map[port.data].add(module)

		for m in module.modules:
			self._prepare_dependency_map(m, mod_source_map, mod_name_map, source_map)

	def _apply_dependencies(self, module, mod_source_map, mod_name_map, source_map):		
		if module in mod_source_map:
			module.depends = set()

			# explicit dependencies
			if module.model.depends is not None:
				for dep_mod_name in module.model.depends:
					dep_mod_id = "{}.{}".format(module.parent.namespace, dep_mod_name)
					if dep_mod_id not in mod_name_map:
						raise Exception("Module {} depends on a non existent module: {}". format(module.id, dep_mod_id))
					dep_mod = mod_name_map[dep_mod_id]
					module.depends.add(dep_mod)
					dep_mod.notify.add(module)

			# implicit dependencies
			for source in mod_source_map[module]:
				dep_mods = source_map[source]
				module.depends.update(dep_mods)
				for dep_mod in dep_mods:
					dep_mod.notify.add(module)

			module.waiting = set(module.depends)

		for m in module.modules:
			self._apply_dependencies(m, mod_source_map, mod_name_map, source_map)

	def _calculate_priorities(self, module, parent_priority = 0, factor = 1.0):
		if module.model.priority is not None:
			priority = module.model.priority
		else:
			priority = 0.5

		module.priority = parent_priority + (priority / factor)
		module.priority_factor = factor

		factor *= 10.0

		for m in module.modules:
			self._calculate_priorities(m, module.priority, factor)

	def schedule_tasks(self):
		tasks = []
		require_rescheduling = True
		while require_rescheduling:
			require_rescheduling, tasks = \
				self._schedule_tasks(self.root_node, tasks)
		return tasks

	def _schedule_tasks(self, module, tasks):
		require_rescheduling = False
		if module.is_leaf_module:
			if module.state == runstates.READY and len(module.waiting) == 0:
				module.tasks = self._partition_module(module)
				if len(module.tasks) == 0:
					self.change_module_state(module, runstates.FINISHED)
					require_rescheduling = True
					#self._log.debug("FINISHED: {}".format(repr(module)))
				else:
					#TODO self.storage.remove_task(task) ???
					for task in module.tasks:
						self.storage.save_task_config(task)

					tasks += module.tasks
					self.change_module_state(module, runstates.WAITING)
					#self._log.debug("READY: {}".format(repr(module)))
					#self._log.debug("tasks: {}".format(repr(tasks)))
			#TODO elif module.state == runstates.FAILED and retrying:
		else:
			for m in module.modules:
				req_resch, tasks = self._schedule_tasks(m, tasks)
				require_rescheduling |= req_resch

			self.update_module_state_from_children(module, recursive = False)

		return (require_rescheduling, tasks)

	def _partition_module(self, module):
		# Calculate input sizes and the minimum wsize
		psizes = []
		mwsize = sys.maxint
		for port in module.in_ports:
			psize = port.data.size()
			psizes += [psize]
			pwsize = port.wsize
			self._log.debug("{}: size={}, wsize={}".format(port.id, psize, pwsize))
			if pwsize < mwsize:
				mwsize = pwsize

		tasks = []

		if len(psizes) == 0:
			# Submit a task for the module without input ports information
			task = TaskNode(parent = module, index = 0)
			tasks += [task]

			for port in module.out_ports:
				data = port.data.get_partition()
				task.out_port_data.append(data)
		else:
			# Check whether all inputs have the same size
			psize = psizes[0]
			for i in xrange(1, len(psizes)):
				if psizes[i] != psize:
					psize = -1
					break

			# Partition the data on input ports
			if psize == -1:
				num_partitions = 1
				self._log.warn("Unable to partition a module with inputs of different size")
			else:
				if mwsize == 0:
					num_partitions = 1
					self._log.warn("Empty port, no partitioning")
				else:
					num_partitions = int(math.ceil(psize / float(mwsize)))
					maxpar = module.maxpar
					self._log.debug("{}: maxpar={}".format(module.id, maxpar))
					if maxpar > 0 and num_partitions > maxpar:
						mwsize = int(math.ceil(psize / float(maxpar)))
						num_partitions = int(math.ceil(psize / float(mwsize)))
					self._log.debug("{}: num_par={}, psize={}, mwsize={}".format(module.id, num_partitions, psize, mwsize))

			start = 0
			partitions = []
			for i in xrange(num_partitions):
				task = TaskNode(parent = module, index = i)
				tasks += [task]
				end = min(start + mwsize, psize)
				size = end - start
				partitions += [(task, start,  size)]
				self._log.debug("{}[{:04i}]: start={}, end={}, size={}".format(module.id, i, start, end, size))
				start += mwsize

			#self._log.debug(repr(partitions))

			for partition in partitions:
				task, start, size = partition
				for port in module.in_ports:
					data = port.data.get_slice(start, size)
					task.in_port_data.append(data)
				for port in module.out_ports:
					data = port.data.get_partition()
					task.out_port_data.append(data)

		return tasks

	@staticmethod
	def change_module_state(module, state):
		prev_state = module.state
		if prev_state == state:
			return

		module.state = state

		if state == runstates.FINISHED:
			for m in module.notify:
				if module in m.waiting:
					m.waiting.remove(module)

	def update_module_state_from_children(self, module, recursive = True):
		children_states = set()
		for m in module.children:
			children_states.add(m.state)

		prev_state = module.state
		if len(children_states) == 1:
			state = iter(children_states).next()
		else:
			if runstates.FAILED in children_states:
				state = runstates.FAILED
			elif runstates.RUNNING in children_states:
				state = runstates.RUNNING
			elif runstates.WAITING in children_states:
				state = runstates.WAITING
			elif runstates.PAUSED in children_states:
				state = runstates.PAUSED
			elif runstates.READY in children_states:
				state = runstates.READY

		if prev_state != state:
#			sb = [module.id, " : ", str(prev_state)]
#			sb += [" --> ", str(state), "  {", str(", ".join(str(s) for s in children_states)), "}"]
#			if module.parent is not None:
#				sb += [" > ", module.parent.name]
#			self._log.debug("".join(sb))

			self.change_module_state(module, state)

			if recursive and module.parent is not None:
				self.update_module_state_from_children(module.parent)

	def __repr__(self):
		sb = []
		self.repr_level(sb, 0)
		return "".join(sb)

	def repr_level(self, sb, level):
		sb += [self._INDENT * level, "Instance ", self.name, "\n"]
		level += 1
		self.root_node.repr_level(sb, level)
		return level
