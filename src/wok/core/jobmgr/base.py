# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.core.cmd.factory import create_cmd_builder
import os.path
from datetime import timedelta

from wok import logger
from wok.core import runstates
from wok.core.jobmgr.errors import *
from wok.core.cmd.factory import create_cmd_builder

class JobManager(object):

	def __init__(self, name, engine, conf):
		self.name = name
		self.engine = engine
		self.conf = conf

		self.__next_id = 1

		self._log = logger.get_logger(conf.get("log"), name)

		if "work_path" not in self.conf:
			raise Exception("Missing 'work_path' in configuration")

		self._work_path = conf["work_path"]

		self._output_path = self.conf.get("output_path", os.path.join(self._work_path, "output"))

	def _next_id(self):
		id = self.__next_id
		self.__next_id += 1
		return id

	def _prepare_cmd(self, task):
		task_conf = task.conf
		execution = task.parent.execution

		exec_mode = execution.mode

		exec_conf_key = "wok.execution.mode.{}".format(exec_mode)
		if exec_conf_key in task_conf:
			exec_conf = task_conf[exec_conf_key]
		else:
			exec_conf = task_conf.create_element()

		if execution.conf is not None:
			exec_conf.merge(execution.conf)

		cmd_builder = create_cmd_builder(exec_mode, exec_conf)

		cmd, args, env = cmd_builder.prepare(task)

		sb = [cmd, " ", " ".join(args)]
		if len(env) > 0:
			sb += ["\n"]
			for k, v in env.iteritems():
				sb += ["\t", str(k), "=", str(v)]
		self._log.debug("".join(sb))

		return cmd, args, env

	def start(self):
		raise Exception("Unimplemented")

	def submit(self, tasks):
		raise Exception("Unimplemented")

	def state(self, job_ids = None):
		raise Exception("Unimplemented")

	def join(self, job_id):
		raise Exception("Unimplemented")

	def join_all(self, job_ids = None):
		raise Exception("Unimplemented")

	def close(self):
		raise Exception("Unimplemented")

class JobResult(object):
	def __init__(self):
		self.state = None
		self.start_time = 0
		self.end_time = 0
		self.exit_code = 0
		self.exit_message = ""
		self.exception_trace = None

	@property
	def elapsed_time(self):
		return timedelta(seconds = self.end_time - self.start_time)

	def __str__(self):
		return "{} [{}]".format(self.state, self.elapsed_time)


class Job(object):
	def __init__(self, id, task, result = None):
		self.id = id
		self.task = task
		self.state = runstates.WAITING

		if result is None:
			result = JobResult()
		self.result = result
