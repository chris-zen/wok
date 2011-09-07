# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from Queue import PriorityQueue, Empty
import multiprocessing as mp
from threading import Thread, Lock, Condition
import subprocess
import tempfile
import time

from wok import exit_codes
from wok.core import runstates
from wok.core.jobmgr.base import JobManager, Job

class McoreJob(Job):
	def __init__(self, job_id, task):
		Job.__init__(self, job_id, task)


class McoreJobManager(JobManager):
	def __init__(self, engine, conf):
		JobManager.__init__(self, "mcore", engine, conf)

		self._num_cores = self.conf.get("max_cores", mp.cpu_count(), dtype=int)

		self._running = False
		self._threads = []

		self._run_lock = Lock()
		self._run_cvar = Condition(self._run_lock)

		self._jobs = {}

		self._waiting_queue = PriorityQueue()

		self._task_output_files = {}

	def _next_job(self):
		element = None
		while element is None:
			try:
				element = self._waiting_queue.get(timeout=1)
			except Empty:
				element = None

		return element[1]

	def _run(self):
		while True:
			job = self._next_job()
			if job is None:
				break

			result = job.result

			with self._run_lock:
				self._log.debug("Running task [{}] {} ...".format(job.id, job.task.id))

			job.state = runstates.RUNNING

			self.engine.notify()

			task = job.task
			task_id = task.id

			# Prepare command
			cmd, args, env = self._prepare_cmd(task)

			# Run command

			if task_id not in self._task_output_files:
				output_path = self.conf.get("output_path")
				if output_path is None:
					output_file = tempfile.mkstemp(prefix = task_id + "-", suffix = ".txt")[1]
				else:
					output_file = os.path.join(output_path, "{}.txt".format(task_id))

				self._task_output_files[task_id] = output_file

			o = open(self._task_output_files[task_id], "a")

			cwd = self.conf.get("working_directory")

			args = [cmd] + args

			result.start_time = time.time()

			try:
				p = subprocess.Popen(
									args = args,
									stdin=None,
									stdout=o,
									stderr=subprocess.STDOUT,
									cwd=cwd,
									env=env)

				p.wait()

				result.end_time = time.time()

				if p.returncode == 0:
					result.state = job.state = runstates.FINISHED
				else:
					result.state = job.state = runstates.FAILED
				result.exit_code = p.returncode
				result.exit_message = "Task exited with return code {}".format(result.exit_code)

				#TODO take results and update task node

			except Exception as e:
				result.end_time = time.time()

				self._log.exception(e)
				import traceback
				result.state = job.state = runstates.FAILED
				result.exit_code = exit_codes.EXEC_EXCEPTION
				result.exit_message = "Exception {}".format(str(e))
				result.exception_trace = traceback.format_exc()
			finally:
				o.close()

			with self._run_lock:
				if result.state == runstates.FINISHED:
					self._log.debug("Task finished [{}] {}".format(job.id, job.task.id))
				else:
					self._log.debug("Task failed [{}] {}: {}".format(job.id, job.task.id, result.exit_message))
				
				self.engine.notify()
				self._run_cvar.notify()

	def start(self):
		with self._run_lock:
			self._log.info("Starting {} scheduler ...".format(self.name))

		self._running = True

		for i in xrange(self._num_cores):
			thread = Thread(target = self._run, name = "{}-{:02}".format(self.name, i))
			self._threads.append(thread)
			thread.start()

	def submit(self, tasks):
		job_ids = []
		with self._run_lock:
			for task in tasks:
				job_id = self._next_id()
				job_ids += [job_id]
				job = McoreJob(job_id, task)
				self._jobs[job_id] = job
				priority = max(min(1 - task.priority, 1), 0)
				self._waiting_queue.put((priority, job))
		return job_ids

	def state(self, job_ids = None):
		states = []
		with self._run_lock:
			if job_ids is None:
				job_ids = self._jobs.keys()
			elif not isinstance(job_ids, list):
				job_ids = [job_ids]
			for job_id in job_ids:
				states += [(job_id, self._jobs[job_id].state)]
		return states

	def join(self, job_id):
		with self._run_lock:
			if job_id not in self._jobs:
				raise UnknownJob(job_id)

			job = self._jobs[job_id]
			while self._running and job.state not in [runstates.FINISHED, runstates.FAILED]:
				self._run_cvar.wait(2)

			return job.result

	def join_all(self, job_ids = None):
		with self._run_lock:
			if job_ids is None:
				job_ids = self._jobs.keys()

			results = []
			for job_id in job_ids:
				if job_id not in self._jobs:
					raise UnknownJob(job_id)

				job = self._jobs[job_id]
				while self._running and job.state not in [runstates.FINISHED, runstates.FAILED]:
					self._run_cvar.wait(2)

				results += job.result

	def stop(self):
		with self._run_lock:
			self._log.info("Stopping {} scheduler ...".format(self.name))

			self._running = False

			self._run_cvar.notify()

		for i in xrange(self._num_cores):
			self._waiting_queue.put((0, None))

		for thread in self._threads:
			thread.join()

