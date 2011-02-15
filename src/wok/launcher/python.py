import os

from wok.launcher import Launcher

class PythonLauncher(Launcher):
	def __init__(self, conf):
		Launcher.__init__(self, conf)

	def template(self, exec_conf, task):
		task_conf = task["conf"]
		
		def_path = task_conf.get("wok.def_path", os.getcwd())
		
		python_bin = self.conf.get("bin", "python")
		python_path = self.conf.get("pythonpath", def_path)

		if "script" not in exec_conf:
			raise Exception("Python launcher requires 'script' configuration")

		script = exec_conf["script"]

		if not os.path.isabs(script):
			script_path = def_path
			script = os.path.join(script_path, script)

		cmd = "%s %s" % (python_bin, script)

		args = []
		#args += [task["id"]]
		args += ["-c", task["__doc_path"]]
		
		if "env" in self.conf:
			shell_env = self.conf["env"]
		else:
			shell_env = self.conf.create_element()

		shell_env["PYTHONPATH"] = python_path
		
		if "env" in exec_conf:
			shell_env.copy_from(exec_conf["env"])
	
		env = shell_env.to_native()
		
		return (None, cmd, args, env)
