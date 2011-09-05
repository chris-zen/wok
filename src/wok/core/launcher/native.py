# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

import os.path

from wok.element import DataElement
from wok.core.launcher import Launcher
from wok.core.launcher.errors import *

class UnknownNativeLauncherLanguage(Exception):
	def __init__(self, lang):
		Exception.__init__(self, "Unknown native launcher language: {}".format(lang))


class NativeLauncher(Launcher):
	def __init__(self, conf):
		Launcher.__init__(self, conf)

	def prepare(self, task, task_file):
		task_conf = task.conf
		
		exe = task.execution

		exe_conf = exe.conf
		if exe_conf is None:
			exe_conf = DataElement()

		if "path" not in exe_conf:
			raise MissingRequiredOption("path")

		lang = exe_conf.get("language", "python")
		if lang in self.conf:
			lang_conf = self.conf[lang]
		else:
			lang_conf = DataElement()

		if "env" in self.conf:
			env = self.conf["env"]
		else:
			env = DataElement()

		if lang == "python":
			cmd = lang_conf.get("bin", "python")
			args = [self._task_absolute_path(task, exe_conf["path"])]
			# TODO lib_path should be appended to sys.path by the task script
#			if "lib_path" in lang_conf:
#				if "PYTHONPATH" in env:
#					env["PYTHONPATH"] = ":".join(lang_conf["lib_path"]) + ":" + env["PYTHONPATH"]
#				else:
#					env["PYTHONPATH"] = ":".join(lang_conf["lib_path"])
		else:
			raise UnknownNativeLauncherLanguage(lang)

		args += ["-c", task_file]

		return cmd, args, env

	@staticmethod
	def _task_absolute_path(task, path):
		if os.path.isabs(path):
			return path

		flow_path = os.path.dirname(task.parent.flow_path)
		return os.path.abspath(os.path.join(flow_path, path))
