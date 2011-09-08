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

class SfsStorage(Storage):

	def __init__(self, context, conf):
		Storage.__init__(self, context, conf, "sfs")

		self.work_path = conf.get("work_path", os.path.join(os.getcwd(), "wok"))
		self.execution_path = conf.get("execution_work_path", self.work_path)
		self.server_path = conf.get("server_work_path", self.execution_path)

		self.update_context(context)

	def update_context(self, context):
		if context == StorageContext.SERVER:
			self.work_path = self.server_path
		else:
			self.work_path = self.execution_path

	@property
	def basic_conf(self):
		c = DataElement()
		c["type"] = self.name
		c["work_path"] = self.work_path
		return c

	def save_task_config(self, task):
		#task_path = os.path.join(self.work_path, "tasks", task.id)
		task_path = os.path.join(self.work_path, task.instance.name, task.parent.name)

		if not os.path.isdir(task_path):
			try:
				os.makedirs(task_path)
			except:
				if not os.path.isdir(task_path):
					self._log.error("Failed creating task path: " + task_path)
					raise

		task_config_path = os.path.join(task_path, "%06d.json" % task.index)

		e = self._task_config_to_element(task)
		try:
			f = open(task_config_path, "w")
			json.dump(e, f, sort_keys=True, indent=4, cls=DataElementJsonEncoder)
			f.close()
		except:
			self._log.error("Failed creating task config file: " + task_config_path)
			raise

	def load_task_config(self, instance_name, module_name, task_index):
		#task_path = os.path.join(self.work_path, "tasks", task_id)
		task_path = os.path.join(self.work_path, instance_name, module_name)
		task_config_path = os.path.join(task_path, "%06d.json" % task_index)

		try:
			f = open(task_config_path, "r")
			o = json.load(f)
			e = DataFactory.from_native(o, key_sep = "/")
			f.close()
		except:
			self._log.error("Failed reading task configuration: " + task_config_path)
			raise

		return e
