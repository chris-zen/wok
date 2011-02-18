import os
import shutil
import shlex
import subprocess as sp
	
import multiprocessing as mp

from wok import logger
from wok.scheduler import JobScheduler
from wok.launcher.factory import create_launcher

def _run_job(job):
	retcode = -128

	o = open(job["output_path"], "wa")

	try:
		args = shlex.split(str(job["cmd"]))

		p = sp.Popen(
					args = args,
					stdin=None,
					stdout=o,
					stderr=sp.STDOUT,
					cwd=job["working_directory"],
					env=job["env"])

		p.wait()

		retcode = p.returncode
	except:
		#import traceback
		#o.write(">>> Exception on job runner:\n")
		#traceback.print_exc(file=o)
		pass
	finally:
		o.close()

	return retcode

class McoreJobScheduler(JobScheduler):
	def __init__(self, conf):
		JobScheduler.__init__(self, conf)
		
		mf = conf.missing_fields(["work_path"])
		if len(mf) > 0:
			raise Exception("Missing configuration: [%s]" % ", ".join(mf))

		self._log = logger.get_logger(conf, "mcore")

		self._work_path = conf["work_path"]
		self._stdio_path = conf.get("io_path", os.path.join(self._work_path, "io"))
		if not os.path.exists(self._stdio_path):
			os.makedirs(self._stdio_path)

		self._working_directory = conf.get("working_directory", None)
		
		self._autorm_io = conf.get("auto_remove.io", False, dtype=bool)

		self._waiting = []

		self._num_proc = conf.get("max_proc", mp.cpu_count(), dtype=int)

		self._pool = mp.Pool(self._num_proc)
		
		self._log.debug("Multi-core scheduler initialized with %i processors" % self._num_proc)

	def clean(self):
		for path in [self._stdio_path]:
			if os.path.exists(path):
				self._log.debug(path)
				shutil.rmtree(path)
			os.makedirs(path)

	def submit(self, task):
		#job_name = task["id"]
		
		execution = task["exec"]
		launcher_name = execution.get("launcher", None)
		if "conf" in execution:
			exec_conf = execution["conf"]
		else:
			exec_conf = execution.create_element()

		task_conf = task["conf"]
		launcher_conf_key = "wok.launchers.%s" % launcher_name
		if launcher_conf_key in task_conf:
			launcher_conf = task_conf[launcher_conf_key]
		else:
			launcher_conf = task_conf.create_element()

		launcher = create_launcher(launcher_name, launcher_conf)

		shell, cmd, args, env = launcher.template(exec_conf, task)

		if shell is None:
			shell = "/bin/sh"

		shell_cmd = " ".join([cmd] + args)

		output_path = os.path.join(self._stdio_path, "%s.io" % task["id"])

		sb = ["%s %s" % (cmd, " ".join(args))]
		if len(env) > 0:
			sb += ["\n"]
			for k, v in env.iteritems():
				sb += ["\t%s=%s" % (k, v)]
		self._log.debug("".join(sb))
		
		job = {}
		job["cmd"] = shell_cmd
		job["output_path"] = output_path
		job["working_directory"] = self._working_directory
		job["env"] = env
	
		result = self._pool.apply_async(_run_job, [job])

		self._waiting += [(job, task, result)]
		
		self._log.info("Task %s submited" % task["id"])

	def wait(self):
		tasks = []
		
		for job, task, result in self._waiting:
			tasks += [task]

			try:
				status_code = result.get()

				io_path = job["output_path"]
				if self._autorm_io and os.path.exists(io_path):
					os.remove(io_path)

				sb = ["Task %s exited with return code %i" % (task["id"], status_code)]
				status_msg = "".join(sb)
				self._log.debug(status_msg)

				task["job/status/code"] = status_code
				task["job/status/msg"] = status_msg
			except Exception as e:
				self._log.exception(e)
				task["job/status/code"] = -1
				task["job/status/msg"] = "There was an exception while waiting for the process to finish: %s" % e

		self._waiting = []
		
		return tasks

	def exit(self):
		self._pool.close()
		self._pool.join()

