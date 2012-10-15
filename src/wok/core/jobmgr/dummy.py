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

import time
from random import random
from Queue import PriorityQueue
import multiprocessing as mp
from threading import Thread, Lock, Condition

from wok.core import runstates
from wok.core.jobmgr import JobManager, Job

class DummyJob(Job):
	def __init__(self, job_id, task):
		Job.__init__(self, job_id, task)


class DummyJobManager(JobManager):
	def __init__(self, engine, conf):
		JobManager.__init__(self, "dummy", engine, conf)

		self._num_cores = self.conf.get("max_cores", mp.cpu_count(), dtype=int)

		self._delay = self.conf.get("delay", 1, dtype=int)
		self._min_delay = self.conf.get("min_delay", self._delay, dtype=int)
		self._max_delay = self.conf.get("max_delay", self._delay, dtype=int)
		self._max_delay = max(self._min_delay, self._max_delay)
		self._tick = self.conf.get("tick", 0.2, dtype=float)
		self._error_ratio = self.conf.get("error_ratio", 0, dtype=float)

		self._running = False
		self._threads = []

		self._run_lock = Lock()
		self._run_cvar = Condition(self._run_lock)

		self._jobs = {}
		
		self._waiting_queue = PriorityQueue()

	def _run(self):
		while True:
			job = self._waiting_queue.get()[1]
			if job is None:
				break

			result = job.result

			delay = self._min_delay + (self._max_delay - self._min_delay) * random()

			with self._run_lock:
				self._log.debug("Simulating task [{}] {} for {:.1f} seconds ...".format(job.id, job.task.id, delay))

			job.state = runstates.RUNNING

			self.engine.notify()

			result.start_time = time.time()

			tick = 0.2
			while delay > 0 and self._running:
				time.sleep(tick)
				delay -= tick

			if random() < self._error_ratio:
				# TODO simulate an exception
				pass

			result.end_time = time.time()

			result.state = job.state = runstates.FINISHED
			
			self.engine.notify()
			
			with self._run_lock:
				self._log.debug("Finished task [{}] {} ...".format(job.id, job.task.id))
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
				job = DummyJob(job_id, task)
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
			while self._running and job.state not in [runstates.FINISHED, runstates.FINISHED]:
				self._run_cvar.wait(4)

	def join_all(self, job_ids = None):
		with self._run_lock:
			if job_ids is None:
				job_ids = self._jobs.keys()

			for job_id in job_ids:
				if job_id not in self._jobs:
					raise UnknownJob(job_id)

				job = self._jobs[job_id]
				while self._running and job.state not in [runstates.FINISHED, runstates.FINISHED]:
					self._run_cvar.wait(4)

	def stop(self):
		with self._run_lock:
			self._log.info("Stopping {} scheduler ...".format(self.name))

			self._running = False

			self._run_cvar.notify()

		for i in xrange(self._num_cores):
			self._waiting_queue.put((0, None))

		for thread in self._threads:
			thread.join()
