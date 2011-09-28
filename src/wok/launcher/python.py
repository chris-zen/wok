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

from wok.launcher import Launcher

class PythonLauncher(Launcher):
	def __init__(self, conf):
		Launcher.__init__(self, conf)

	def template(self, exec_conf, task):
		task_conf = task["conf"]
		
		flow_path = task_conf.get("wok.__flow.path", os.getcwd())
		
		python_bin = self.conf.get("bin", "python")

		python_path = [flow_path]
		if "pythonpath" in self.conf:
			pp = self.conf["pythonpath"].to_native()
			if isinstance(pp, list):
				python_path += pp
			else:
				python_path += [pp]

		if "pythonpath" in exec_conf:
			python_path += [exec_conf["pythonpath"]]

		if "script" not in exec_conf:
			raise Exception("Python launcher requires 'script' configuration")

		script = exec_conf["script"]

		if not os.path.isabs(script):
			script = os.path.join(flow_path, script)

		cmd = "%s %s" % (python_bin, script)

		args = []
		args += ["-c", task["__doc_path"]]
		
		if "env" in self.conf:
			shell_env = self.conf["env"]
		else:
			shell_env = self.conf.create_element()

		shell_env["PYTHONPATH"] = ":".join(python_path)
		
		if "env" in exec_conf:
			shell_env.copy_from(exec_conf["env"])
	
		env = shell_env.to_native()
		
		return (None, cmd, args, env)
