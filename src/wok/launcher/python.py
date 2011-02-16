import os

from wok.launcher import Launcher

class PythonLauncher(Launcher):
	def __init__(self, conf):
		Launcher.__init__(self, conf)

	def template(self, exec_conf, task):
		task_conf = task["conf"]
		
		flow_path = task_conf.get("wok.flow_path", os.getcwd())
		
		python_bin = self.conf.get("bin", "python")

		python_path = [flow_path]
		if "pythonpath" in self.conf:
			python_path += [self.conf["pythonpath"]]

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
