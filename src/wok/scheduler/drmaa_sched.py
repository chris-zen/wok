import drmaa
import os
import shutil
from stat import S_IRUSR, S_IWUSR, S_IXUSR, S_IRGRP, S_IWGRP, S_IXGRP, S_IROTH, S_IWOTH, S_IXOTH

from wok import logger
from wok.scheduler import JobScheduler
from wok.launcher.factory import create_launcher

class DrmaaJobScheduler(JobScheduler):
	def __init__(self, conf):
		JobScheduler.__init__(self, conf)
		
		mf = conf.missing_fields(["work_path"])
		if len(mf) > 0:
			raise Exception("Missing configuration: [%s]" % ", ".join(mf))

		self._log = logger.get_logger(conf, "drmaa")

		self._work_path = conf["work_path"]
		self._stdio_path = conf.get("io_path", os.path.join(self._work_path, "io"))
		if not os.path.exists(self._stdio_path):
			os.makedirs(self._stdio_path)
		self._shell_path = os.path.join(self._work_path, "sh")
		if not os.path.exists(self._shell_path):
			os.makedirs(self._shell_path)

		self._working_directory = conf.get("working_directory", None)
		
		self._autorm_sh = conf.get("auto_remove.sh", True, dtype=bool)
		self._autorm_io = conf.get("auto_remove.io", True, dtype=bool)

		self._session = drmaa.Session()
		self._session.initialize()
		
		sb = ["DRMAA initialized:\n"]
		sb += ["\tSupported contact strings: %s\n" % self._session.contact]
		sb += ["\tSupported DRM systems: %s\n" % self._session.drmsInfo]
		sb += ["\tSupported DRMAA implementations: %s\n" % self._session.drmaaImplementation]
		sb += ["\tVersion %s" % str(self._session.version)]
		self._log.debug("".join(sb))

		self._waiting = []
		self._jobs = {}

	def clean(self):
		for path in [self._stdio_path, self._shell_path]:
			if os.path.exists(path):
				self._log.debug(path)
				shutil.rmtree(path)
			os.makedirs(path)

	def _create_shell(self, task, shell, cmd):
		if shell is None:
			shell = "/bin/bash"

		shell_script = os.path.join(self._shell_path, "%s.sh" % task["id"])
		f = open(shell_script, "w")
		f.write("#!%s\n" % shell)
		f.write("%s $*\n" % cmd)
		f.close()
		os.chmod(shell_script, S_IRUSR | S_IWUSR | S_IXUSR | S_IRGRP | S_IWGRP | S_IXGRP | S_IROTH | S_IWOTH | S_IXOTH)
		return shell_script

	def submit(self, task):
		job_name = task["id"]
		
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

		shell_cmd = self._create_shell(task, shell, cmd)
		
		output_path = os.path.join(self._stdio_path, "%s.io" % task["id"])
		
		jt = self._session.createJobTemplate()
		jt.jobName = job_name
		jt.remoteCommand = shell_cmd
		jt.args = args
		jt.jobEnvironment = env
		jt.outputPath = ":" + output_path
		jt.joinFiles = True
		if self._working_directory is not None:
			jt.workingDirectory = self._working_directory
		
		sb = ["%s %s" % (cmd, " ".join(args))]
		if len(env) > 0:
			sb += ["\n"]
			for k, v in env.iteritems():
				sb += ["\t%s=%s" % (k, v)]
		self._log.debug("".join(sb))
		
		jobid = self._session.runJob(jt)
		self._waiting += [jobid]
		self._jobs[jobid] = {
			"task" : task,
			"sh_path" : shell_cmd,
			"io_path" : output_path
		}
		
		task["job"] = job_conf = task.create_element()
		job_conf["id"] = jobid
		job_conf["job_name"] = job_name
		job_conf["command"] = cmd
		job_conf["args"] = job_conf.create_list(args)
		job_conf["env"] = job_conf.create_element(env)
		job_conf["output_path"] = output_path
		if self._working_directory is not None:
			job_conf["working_dir"] = self._working_directory
		
		self._log.info("Task %s submited as job %s." % (task["id"], jobid))
		
		self._session.deleteJobTemplate(jt)
	
	def wait(self):
		tasks = []
		
		self._session.synchronize(self._waiting, drmaa.Session.TIMEOUT_WAIT_FOREVER, False)
		for jobid in self._waiting:
			job = self._jobs[jobid]
			task = job["task"]
			tasks += [task]

			try:
				ret = self._session.wait(jobid, drmaa.Session.TIMEOUT_WAIT_FOREVER)
			
				sh_path = job["sh_path"]
				io_path = job["io_path"]
				del self._jobs[jobid]

				if self._autorm_sh:
					os.remove(sh_path)

				if self._autorm_io:
					os.remove(io_path)

				status_code = -1
				sb = ["Task %s (job %s)" % (task["id"], jobid)]
				if ret.wasAborted:
					sb += [" was aborted"]
					if ret.hasCoreDump:
						sb += [" with core dump"]
				elif ret.hasExited:
					sb += [" has exited with status %s" % ret.exitStatus]
					status_code = ret.exitStatus
				elif ret.hasSignal:
					sb += [" got signal %s" % ret.terminatedSignal]
				status_msg = "".join(sb)
				self._log.debug(status_msg)

				task["job/status/code"] = status_code
				task["job/status/msg"] = status_msg
			except Exception as e:
				self._log.exception(e)
				task["job/status/code"] = -1
				task["job/status/msg"] = "There was an exception while waiting for the job to finish: %s" % e
			
		self._waiting = []
		
		return tasks

	def exit(self):
		self._session.exit()

