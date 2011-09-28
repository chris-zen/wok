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

from wok.launcher import Launcher

class ShellLauncher(Launcher):
	def __init__(self, conf):
		Launcher.__init__(self, conf)
		
	def template(self, exec_conf, task):
		#task_conf = task["conf"]
		#flow_path = task_conf.get("wok.__flow.path", os.getcwd())
		
		shell = self.conf.get("bin", "sh")

		if "cmd" not in exec_conf:
			raise Exception("Shell launcher requires 'cmd' configuration")

		cmd = exec_conf["cmd"]

		args = [task["id"]]
		
		if "env" in self.conf:
			shell_env = self.conf["env"]
		else:
			shell_env = self.conf.create_element()

		if "env" in exec_conf:
			shell_env.copy_from(exec_conf["env"])
	
		env = shell_env.to_native()
		
		return (shell, cmd, args, env)
