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

	# Logs =====================================================================

	def append_logs(self, instance_name, module_path, task_index):
		if context != StorageContext.CONTROLLER:
			raise Exception()
	
	def query_logs(self, instance_name, module_path, task_index):
		#TODO
		return None

	# Ports ====================================================================

	def create_port_data(self, port):
		mod_path = self._module_path(port.parent)
		port_path = os.path.join(mod_path, port.name)
		self._ensure_path(port_path)
		e = DataElement(key_sep = "/")
		e["name"] = port.name
		e["module"] = port.parent.id
		return PathData(port.serializer, port_path, port_desc = e)

	def create_port_linked_data(self, port, linked_data):
		return linked_data

	def create_port_joined_data(self, port, joined_data):
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
