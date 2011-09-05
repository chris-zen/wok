# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

import os.path
from datetime import timedelta

from wok import logger
from wok.core import runstates
from wok.core.jobmgr.errors import *

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

	def start(self):
		raise Exception("Unimplemented")

	def clean(self):
		raise Exception("Unimplemented")

	def submit(self, task):
		raise Exception("Unimplemented")

	def state(self, job_ids = None):
		raise Exception("Unimplemented")

	def wait(self, job_ids = None):
		raise Exception("Unimplemented")

	def stop(self):
		raise Exception("Unimplemented")

class JobResult(object):
	def __init__(self):
		self.state = None
		self.start_time = 0
		self.end_time = 0

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
