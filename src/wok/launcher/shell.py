
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
