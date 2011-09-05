# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from Queue import PriorityQueue
import multiprocessing as mp
from threading import Thread, Lock, Condition

from wok.core import runstates
from wok.core.jobmgr.base import JobManager, Job

class DummyJob(Job):
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

	def _run(self):
		while True:
			job = self._waiting_queue.get()[1]
			if job is None:
				break

			result = job.result

			with self._run_lock:
				self._log.debug("Running task [{}] {} ...".format(job.id, job.task.id))

			job.state = runstates.RUNNING

			self.engine.notify()

			# TODO subprocess.call
			self._job_run(job)

			result.state = job.state = runstates.FINISHED

			self.engine.notify()

			with self._run_lock:
				self._log.debug("Finished task [{}] {} ...".format(job.id, job.task.id))
				self._run_cvar.notify()

	def _job_run(self, job):
		task = job.task
		task_id = task.id
		task_conf = task.conf
		execution = task.parent.execution

		# Prepare command

		launcher_name = execution.launcher
		if launcher_name is None:
			launcher_name = DEFAULT_LAUNCHER

		launcher_conf_key = "wok.launchers.{}".format(launcher_name)
		if launcher_conf_key in task_conf:
			launcher_conf = task_conf[launcher_conf_key]
		else:
			launcher_conf = task_conf.create_element()

		launcher = create_launcher(launcher_name, launcher_conf)

		cmd, args, env = launcher.prepare(task, task_file)

		shell_cmd = " ".join([cmd] + args)

		sb = [cmd, " ", " ".join(args)]
		if len(env) > 0:
			sb += ["\n"]
			for k, v in env.iteritems():
				sb += ["\t", str(k), "=", str(v)]
		self._log.debug("".join(sb))

		#import sys
		#sys.stdout.flush()

		# Run command

		o = open(output_file, "a")

		try:
			args = [cmd] + args

			start_time = time.time()

			p = sp.Popen(
						args = args,
						stdin=None,
						stdout=o,
						stderr=sp.STDOUT,
						cwd=working_directory,
						env=env)

			p.wait()

			elapsed_time = time.time() - start_time
			exit_code = p.returncode
			exit_message = "Task {} exited with return code {}".format(task_id, exit_code)

			#TODO take results and update task node
		except:
			import traceback
			exit_code = exit_codes.LAUNCH_EXCEPTION
			exit_message = "Exception launching task {}".format(task_id)
			exit_exception = traceback.format_exc()
		finally:
			o.close()

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
				while self._running and job.state not in [runstates.FINISHED, runstates.FINISHED]:
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

