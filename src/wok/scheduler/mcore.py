# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

import traceback
import os
import shutil
import shlex
import subprocess as sp
import time
	
import multiprocessing as mp

from wok import logger
from wok.scheduler import JobScheduler
from wok.launcher.factory import create_launcher
from wok import exit_codes

def _job_run(job):
	job.run()
	return job

class Job(object):
	def __init__(self):
		self.cmd = None
		self.output_path = None
		self.working_directory = None
		self.env = None
		self.task = None

		self.elapsed_time = 0
		self.exit_code = exit_codes.LAUNCH_EXCEPTION
		self.exit_message = None
		self.exit_exception = None

	def run(self):
		o = open(self.output_path, "a")

		try:
			args = shlex.split(str(self.cmd))

			start_time = time.time()

			p = sp.Popen(
						args = args,
						stdin=None,
						stdout=o,
						stderr=sp.STDOUT,
						cwd=self.working_directory,
						env=self.env)

			p.wait()

			self.elapsed_time = time.time() - start_time
			self.exit_code = p.returncode
			self.exit_message = "Task %s exited with return code %i" % (self.task["id"], self.exit_code)
		except:
			import traceback
			self.exit_code = exit_codes.LAUNCH_EXCEPTION
			self.exit_msg = "Exception launching task %s" % self.task["id"]
			self.exit_exception = traceback.format_exc()
		finally:
			o.close()

class McoreJobScheduler(JobScheduler):
	def __init__(self, conf):
		JobScheduler.__init__(self, conf)
		
		mf = conf.missing_fields(["__work_path"])
		if len(mf) > 0:
			raise Exception("Missing configuration: [%s]" % ", ".join(mf))

		self._log = logger.get_logger(conf.get("log"), "mcore")

		self._work_path = conf["__work_path"]
		#self._output_path = conf.get("__output_path", os.path.join(self._work_path, "output"))
		#if not os.path.exists(self._output_path):
		#	os.makedirs(self._output_path)

		self._working_directory = conf.get("working_directory", None)
		
		self._autorm_output = conf.get("auto_remove.output", False, dtype=bool)

		self._waiting = []

		self._num_proc = conf.get("max_proc", mp.cpu_count(), dtype=int)

		self.init() #TODO this should be done by wok

	def init(self):
		self._log.info("Initializing multi-core scheduler ...")

		self._pool = mp.Pool(self._num_proc)

		self._log.debug("Multi-core scheduler initialized with %i processors" % self._num_proc)

	def clean(self):
		#for path in [self._work_path]:
		#	if os.path.exists(path):
		#		self._log.debug(path)
		#		shutil.rmtree(path)
		#	os.makedirs(path)
		#TODO remove only sh files as tasks finish
		pass

	def submit(self, task):
		
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

		output_path = task["job/output_path"]

		sb = ["%s %s" % (cmd, " ".join(args))]
		if len(env) > 0:
			sb += ["\n"]
			for k, v in env.iteritems():
				sb += ["\t%s=%s" % (k, v)]
		self._log.debug("".join(sb))

		#print shell_cmd
		#import sys
		#sys.stdout.flush()
		
		job = Job()
		job.name = task["id"]
		job.cmd = shell_cmd
		job.output_path = output_path
		job.working_directory = self._working_directory
		job.env = env
		job.task = task

		result = self._pool.apply_async(_job_run, [job])

		self._waiting += [(job, result)]
		
		self._log.info("Task %s submited" % task["id"])

	def wait(self, timeout = None):
		tasks = []

		timeout_raised = False
		start_time = time.time()

		while len(self._waiting) > 0 and not timeout_raised:
			finished = []
			for job, result in self._waiting:
				task = job.task

				elapsed_time = time.time() - start_time
				timeout_raised = timeout is not None and elapsed_time >= timeout
				try:
					if timeout is not None:
						result_timeout = min(1, max(0, timeout - elapsed_time))
						rjob = result.get(timeout = result_timeout)
					else:
						rjob = result.get()

					if rjob is not None:
						finished += [(job, result)]
						tasks += [task]
						output_path = rjob.output_path
						if self._autorm_output and os.path.exists(output_path):
							os.remove(output_path)

						task["job/elapsed_time"] = rjob.elapsed_time
						task["job/exit/code"] = rjob.exit_code
						task["job/exit/message"] = rjob.exit_message
						if rjob.exit_exception is not None:
							task["job/exit/exception"] = rjob.exit_exception

				except Exception as e:
					self._log.exception(e)

					task["job/exit/code"] = -128
					task["job/exit/message"] = "Exception waiting for the task %s to finish: %s" % (task["id"], e)
					task["job/exit/exception"] = traceback.format_exc()

				if timeout_raised:
					break

			for job_result in finished:
				self._waiting.remove(job_result)

		return tasks

	def finished(self):
		return len(self._waiting) == 0
	
	def exit(self):
		self._pool.close()
		self._pool.join()
