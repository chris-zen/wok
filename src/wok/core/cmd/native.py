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

import os.path

from wok.element import DataElement
from wok.core.cmd.base import CmdBuilder
from wok.core.cmd.errors import *

class UnknownNativeCmdBuilderLanguage(Exception):
	def __init__(self, lang):
		Exception.__init__(self, "Unknown native command builder language: {}".format(lang))

class NativeCmdBuilder(CmdBuilder):
	def __init__(self, conf):
		CmdBuilder.__init__(self, conf)

	def _merge_env(self, env1, env2):
		env = DataElement()
		if env1 is not None:
			env.merge(env1)
		if env2 is not None:
			env.merge(env2)
		return env

	def _storage_conf(self, value, path = None):		
		if path is None:
			path = []

		if not isinstance(value, DataElement):
			yield (".".join(path), value)
		else:
			for key in value.keys():
				for k, v in self._storage_conf(value[key], path + [key]):
					yield (k, v)

	def prepare(self, task):
		wok_conf = task.instance.conf.get("wok")
		if wok_conf is None:
			wok_conf = DataElement()

		lang = self.conf.get("language", "python")

		lang_key = "execution.mode.native.{}".format(lang)
		if lang_key in wok_conf:
			lang_conf = wok_conf[lang_key]
		else:
			lang_conf = DataElement()

		if "script_path" not in self.conf:
			raise MissingRequiredOption("script_path")

		script_path = self.conf["script_path"]

		if lang == "python":
			cmd = lang_conf.get("bin", "python")
			args = [self._task_absolute_path(task, script_path)]
			env = self._merge_env(lang_conf.get("env"), self.conf.get("env"))

			if "lib_path" in lang_conf:
				if "PYTHONPATH" in env:
					env["PYTHONPATH"] = ":".join(lang_conf["lib_path"]) + ":" + env["PYTHONPATH"]
				else:
					env["PYTHONPATH"] = ":".join(lang_conf["lib_path"])
		else:
			raise UnknownNativeCmdBuilderLanguage(lang)

		args += ["-D", "instance_name=" + task.instance.name,
				"-D", "module_path=" + ".".join([task.parent.namespace, task.parent.name]),
				"-D", "task_index=" + str(task.index)]

		for key, value in self._storage_conf(task.instance.engine.storage.basic_conf):
			args += ["-D", "storage.{}={}".format(key, value)]

		return cmd, args, env.to_native()

	@staticmethod
	def _task_absolute_path(task, path):
		if os.path.isabs(path):
			return path

		flow_path = os.path.dirname(task.parent.flow_path)
		return os.path.abspath(os.path.join(flow_path, path))
