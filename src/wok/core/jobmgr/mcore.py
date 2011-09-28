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

import os
import os.path
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
		self._kill_threads = False
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

			task = job.task
			task_id = task.id
			
			result = job.result

			with self._run_lock:
				self._log.debug("Running task [{}] {} ...".format(job.id, job.task.id))

			job.state = runstates.RUNNING

			self.engine.notify()

			# Prepare command
			cmd, args, env = self._prepare_cmd(task)

			# Run command

			if task_id not in self._task_output_files:
				work_path = self.conf.get("work_path")
				if work_path is not None:
					work_path = os.path.abspath(work_path)
				else:
					work_path = tempfile.mkdtemp(prefix = "wok-")

				default_output_path = os.path.join(work_path, "output")
				if not os.path.exists(default_output_path):
					os.makedirs(default_output_path)

				output_path = self.conf.get("output_path", default_output_path)
				output_file = os.path.abspath(os.path.join(
								output_path, "{}.txt".format(task_id)))

				self._task_output_files[task_id] = (work_path, output_file)

			o = open(self._task_output_files[task_id][1], "a")

			cwd = self.conf.get("working_directory")
			if cwd is not None:
				cwd = os.path.abspath(cwd)

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

				while not self._kill_threads and p.poll() is None:
					time.sleep(1)

				if self._kill_threads:
					p.terminate()
					self._log.warn("Not waiting for Popen.terminate(). Should I do?")
					o.close()
					return

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
					sb = ["Task failed [{}] {}: {}".format(job.id, job.task.id, result.exit_message)]
					if result.exception_trace is not None:
						sb += ["\n", result.exception_trace]
					self._log.error("".join(sb))

				self._run_cvar.notify()

			self.engine.notify()

	def start(self):
		with self._run_lock:
			self._log.info("Starting job manager [{}] ...".format(self.name))

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

			del self._jobs[job_id]

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

				del self._jobs[job_id]
				results += [(job_id, job.result)]
		
		return results


	def close(self):
		with self._run_lock:
			self._log.info("Stopping job manager [{}] ...".format(self.name))

			self._running = False
			self._kill_threads = False

			self._run_cvar.notify()

		for _ in xrange(self._num_cores):
			self._waiting_queue.put((0, None))

		for thread in self._threads:
			timeout = 30
			while thread.isAlive():
				thread.join(1)
				timeout -= 1
				if timeout == 0:
					self._kill_threads = True

		with self._run_lock:
			self._log.info("[{}] stopped".format(self.name))
