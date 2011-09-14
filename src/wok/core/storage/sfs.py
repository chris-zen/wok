# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

import os
import os.path
import json

from wok.element import DataElement, DataFactory, DataElementJsonEncoder
from wok.core.storage.base import Storage, StorageContext

from wok.core.portio.filedata import FileData
from wok.core.portio.pathdata import PathData
from wok.core.portio.multidata import MultiData

_PORT_DATA_TYPES = {
	FileData.TYPE_NAME : FileData,
	PathData.TYPE_NAME : PathData,
	MultiData.TYPE_NAME : MultiData
}

class SfsStorage(Storage):
	"""
	Implements Storage interface for a Shared File System (i.e. NFS).
	The file system is shared and visible for all the execution nodes and the wok controller.
	"""

	def __init__(self, context, conf):
		Storage.__init__(self, context, conf, "sfs")

		self.work_path = conf.get("work_path", os.path.join(os.getcwd(), "wok"))
		self.execution_path = conf.get("execution_work_path", self.work_path)
		self.controller_path = conf.get("controller_work_path", self.execution_path)

		self.update_context(context)

	def _ensure_path(self, path):
		if not os.path.isdir(path):
			try:
				os.makedirs(path)
			except:
				if not os.path.isdir(path):
					self._log.error("Failed creating path: " + path)
					raise

	def _module_path(self, mod):
		mod_path = os.path.join(
						self.work_path,
						mod.instance.name,
						os.path.join(*mod.namespace.split(".")),
						mod.name)

		self._ensure_path(mod_path)

		return mod_path

	# ==========================================================================

	def update_context(self, context):
		"Updates the internal configuration according to the new context"

		if context == StorageContext.CONTROLLER:
			self.work_path = self.controller_path
		else:
			self.work_path = self.execution_path

	@property
	def basic_conf(self):
		"Return the basic configuration needed to start a task execution"

		c = DataElement()
		c["type"] = self.name
		c["work_path"] = self.work_path
		return c

	# Tasks ====================================================================

	def save_task_config(self, task):
		"Save a task configuration"

		mod_path = self._module_path(task.parent)

		task_config_path = os.path.join(mod_path, "%06d.task" % task.index)

		e = self._task_config_to_element(task)
		try:
			f = open(task_config_path, "w")
			json.dump(e, f, sort_keys=True, indent=4, cls=DataElementJsonEncoder)
			f.close()
		except:
			self._log.error("Failed creating task config file: " + task_config_path)
			raise

	def load_task_config(self, instance_name, module_path, task_index):
		"Load a task configuration"

		mod_path = os.path.join(
						self.work_path,
						instance_name,
						os.path.join(*module_path.split(".")))
						
		task_config_path = os.path.join(mod_path, "%06d.task" % task_index)

		try:
			f = open(task_config_path, "r")
			o = json.load(f)
			e = DataFactory.from_native(o, key_sep = "/")
			f.close()
		except:
			self._log.error("Failed reading task configuration: " + task_config_path)
			raise

		return e

	# Ports ====================================================================

	def create_port_data(self, port):
		mod_path = self._module_path(port.parent)
		port_path = os.path.join(mod_path, port.name)
		self._ensure_path(port_path)
#		port_config_file = os.path.join(mod_path, port.name + ".port")
#		e = DataElement(key_sep = "/")
#		e["type"] = "data"
#		try:
#			f = open(port_config_file, "w")
#			json.dump(e, f, sort_keys=True, indent=4, cls=DataElementJsonEncoder)
#			f.close()
#		except:
#			self._log.error("Failed creating port config file: " + port_config_path)
#			raise
		e = DataElement(key_sep = "/")
		e["name"] = port.name
		e["module"] = port.parent.id
		return PathData(port.serializer, port_path, port_desc = e)

	def create_port_linked_data(self, port, linked_data):
#		mod_path = self._module_path(port.parent)
#		port_config_file = os.path.join(mod_path, port.name + ".port")
#		e = DataElement(key_sep = "/")
#		e["type"] = "linked"
#		e["module"] = linked_port.parent.id
#		e["port"] = linked_port.name
#		try:
#			f = open(port_config_file, "w")
#			json.dump(e, f, sort_keys=True, indent=4, cls=DataElementJsonEncoder)
#			f.close()
#		except:
#			self._log.error("Failed creating port config file: " + port_config_path)
#			raise
		return linked_data

	def create_port_joined_data(self, port, joined_data):
#		mod_path = self._module_path(port.parent)
#		port_config_file = os.path.join(mod_path, port.name + ".port")
#		e = DataElement(key_sep = "/")
#		e["type"] = "joined"
#		l = e.create_list("ports")
#		data = []
#		for joined_port in joined_ports:
#			data.append(joined_port.data)
#			p = e.create_element()
#			p["module"] = joined_port.parent.id
#			p["port"] = joined_port.name
#			l.append(p)
#		try:
#			f = open(port_config_file, "w")
#			json.dump(e, f, sort_keys=True, indent=4, cls=DataElementJsonEncoder)
#			f.close()
#		except:
#			self._log.error("Failed creating port config file: " + port_config_path)
#			raise
		e = DataElement(key_sep = "/")
		e["name"] = port.name
		e["module"] = port.parent.id
		return MultiData(joined_data, port_desc = e)

	def create_port_data_from_file(self, path):
		raise Exception("Unimplemented")

	def create_port_data_from_conf(self, port_conf):
		if "type" not in port_conf:
			raise Exception("Missing port type: " + repr(port_conf))

		type = port_conf["type"]
		if type not in [FileData.TYPE_NAME, PathData.TYPE_NAME, MultiData.TYPE_NAME]:
			raise Exception("Unknown port type: " + type)

		#self._log.debug("Creating port data: type=%s, conf=%s" % (type, repr(port_conf)))
		pdata = _PORT_DATA_TYPES[type](conf = port_conf,
					factory = self.create_port_data_from_conf)

		return pdata
	
#	def load_port_data(self, instance_name, module_path, port_name):
#		mod_path = os.path.join(
#						self.work_path,
#						instance_name,
#						os.path.join(*module_path.split(".")))
#		port_path = os.path.join(mod_path, port_name)
#
#		raise Exception("Unimplemented")
