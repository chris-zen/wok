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
import re

from Queue import Queue, Empty
from threading import Thread, Condition
from multiprocessing import cpu_count

from wok import logger
from wok.element import DataList
from wok.config import ConfigBuilder
from wok.core import runstates
from wok.core.sync import Synchronizable, synchronized
from wok.core.flow.loader import FlowLoader
from wok.core.instance import Instance, InstanceController
from wok.core.jobmgr.factory import create_job_manager
from wok.core.storage.base import StorageContext
from wok.core.storage.factory import create_storage


# 2011-10-06 18:39:46,849 bfast_localalign-0000 INFO  : hello world
_LOG_RE = re.compile("^(\d\d\d\d-\d\d-\d\d) (\d\d:\d\d:\d\d,\d\d\d) (.*) (DEBUG|INFO|WARN|ERROR) +: (.*)$")

class WokEngine(Synchronizable):
	"""
	The Wok engine manages the execution of workflow instances.
	Each instance represents a workflow loaded with a certain configuration.
	"""

	def __init__(self, conf):
		Synchronizable.__init__(self)

		self.conf = conf

		wok_conf = conf["wok"]

		self._log = logger.get_logger(wok_conf.get("log"), "wok-engine")

		self._work_path = wok_conf.get("work_path", os.path.join(os.getcwd(), "wok"))

		self._flow_path = wok_conf.get("flow_path")
		if self._flow_path is None:
			self._flow_path = [os.curdir]
		elif not isinstance(self._flow_path, (list, DataList)):
			raise Exception('wok.flow_path: A list of paths expected. Example ["path1", "path2"]')

		self._flow_loader = FlowLoader(self._flow_path)
		sb = ["wok.flow_path:\n"]
		for uri, ff in self._flow_loader.flow_files.items():
			sb += ["\t", uri, "\t", ff[0], "\n"]
		self._log.debug("".join(sb))

		self._instances = []
		self._instances_map = {}

		#self._lock = Lock()
		self._cvar = Condition(self._lock)
		
		self._run_thread = None
		self._running = False

		self._job_task_map = {}

		self._logs_threads = []
		self._logs_queue = Queue()

		self._join_thread = None
		self._join_queue = Queue()

		self._notified = False

		self._job_mgr = self._create_job_manager(wok_conf)
		
		self._storage = self._create_storage(wok_conf)

		self._db = SqliteEngineDB(self)

		self._restore_state()

	def _restore_state(self):
		#TODO restore db state
		pass
	
	def _create_job_manager(self, wok_conf):
		jobmgr_name = wok_conf.get("job_manager", "mcore", dtype=str)
		
		jobmgr_conf = wok_conf.create_element()
		if "job_managers.default" in wok_conf:
			jobmgr_conf.merge(wok_conf["job_managers.default"])

		jobmgr_conf_key = ".".join(["job_managers", jobmgr_name])
		if jobmgr_conf_key in wok_conf:
			jobmgr_conf.merge(wok_conf[jobmgr_conf_key])

#		if "__output_path" not in sched_conf:
#			sched_conf["__output_path"] = self._output_path

		if "work_path" not in jobmgr_conf:
			jobmgr_conf["work_path"] = os.path.join(self._work_path, jobmgr_name)

		self._log.debug("Creating '{}' scheduler with configuration {}".format(jobmgr_name, repr(jobmgr_conf)))

		return create_job_manager(jobmgr_name, self, jobmgr_conf)

	@staticmethod
	def _create_storage(wok_conf):
		storage_conf = wok_conf.get("storage")
		if storage_conf is None:
			storage_conf = wok_conf.create_element()

		storage_type = storage_conf.get("type", "sfs")

		if "work_path" not in storage_conf:
			wok_work_path = wok_conf.get("work_path", os.path.join(os.getcwd(), "wok"))
			storage_conf["work_path"] = os.path.join(wok_work_path, "storage")

		return create_storage(storage_type, StorageContext.CONTROLLER, storage_conf)

	@property
	def work_path(self):
		return self._work_path
	
	@property
	def job_manager(self):
		return self._job_mgr

	@property
	def storage(self):
		return self._storage
	
	@property
	def flow_loader(self):
		return self._flow_loader

	@synchronized
	def create_instance(self, inst_name, conf_builder, flow_file):
		"Creates a new workflow instance"

		#TODO check in the db
		if inst_name in self._instances_map:
			raise Exception("Instance with this name already exists: {}".format(inst_name))

		self._log.debug("Creating instance {} from {} ...".format(inst_name, flow_file))

		cb = ConfigBuilder()
		cb.add_value("wok.__instance.name", inst_name)
		cb.add_value("wok.__instance.work_path", os.path.join(self._work_path, inst_name))
		cb.add_builder(conf_builder)

		# Create instance
		inst = Instance(self, inst_name, cb, flow_file)
		try:
			# Initialize instance and register by name
			inst.initialize()
			self._instances += [inst]
			self._instances_map[inst_name] = inst
			self._cvar.notify()

			self._db.instance_persist(inst)
		except:
			self._log.error("Error while creating instance {} for the workflow {} with configuration {}".format(inst_name, flow_file, cb()))
			raise

		self._log.debug("\n" + repr(inst))

		return inst

	def __queue_adaptative_get(self, queue, start_timeout = 1, max_timeout = 4):
		timeout = start_timeout
		msg = None
		while self._running and msg is None:
			try:
				msg = queue.get(timeout=timeout)
			except Empty:
				if timeout < max_timeout:
					timeout += 1
		return msg

	def __queue_batch_get(self, queue, start_timeout = 1, max_timeout = 4):
		timeout = start_timeout
		msg_batch = []
		while self._running and len(msg_batch) == 0:
			try:
				msg_batch += [queue.get(timeout=timeout)]
				while not queue.empty():
					msg_batch += [queue.get(timeout=timeout)]
			except Empty:
				if timeout < max_timeout:
					timeout += 1
		return msg_batch

	@synchronized
	def _run(self):
		self._running = True

		job_mgr = self._job_mgr

		try:
			job_mgr.start()

			# Start the logs threads

			for i in range(cpu_count()):
			#for i in range(1):
				t = Thread(target = self._logs, name = "wok-engine-logs-%d" % i)
				self._logs_threads += [t]
				t.start()

			# Start the join thread

			self._join_thread = Thread(
									target = self._join,
									name = "wok-engine-join")
			self._join_thread.start()

			self._log.info("Engine run thread ready")

			while self._running:

				#self._log.debug("Scheduling new tasks ...")

				# submit tasks ready to be executed
				for inst in self._instances:
					tasks = inst.schedule_tasks()
					if len(tasks) > 0:
						#self._log.debug("ready_tasks:\n" + "\n".join(["\t" + t.id for t in tasks]))
						job_ids = job_mgr.submit(tasks)
						for i, task in enumerate(tasks):
							self._job_task_map[job_ids[i]] = task
							task.job_id = job_ids[i]
				
				#self._log.debug("Waiting for events ...")

				while not self._notified and self._running:
					self._cvar.wait(1)
				self._notified = False

				if not self._running:
					break

				job_states = job_mgr.state()
				
				#self._log.debug("Job states:\n" + "\n".join("\t{}: {}".format(jid, jst) for jid, jst in job_states))

				updated_modules = set()

				# detect tasks which state has changed
				for job_id, state in job_states:
					task = self._job_task_map[job_id]
					if task.state != state:
						task.state = state
						updated_modules.add(task.parent)
						self._log.debug("Task %s changed state to %s" % (task.id, state))

						# if task has finished, queue it for logs retrieval
						# otherwise queue it directly for joining
						if state in [runstates.FINISHED, runstates.FAILED]:
							self._logs_queue.put((task, job_id))
							#self._join_queue.put((task, job_id))

				#self._log.debug("Updating modules state ...\n" + "\n".join("\t{}".format(m.id) for m in sorted(updated_modules)))
				#self._log.debug("Updating modules state ...")

				# update affected modules state
				updated_instances = set()
				for m in updated_modules:
					inst = m.instance
					inst.update_module_state_from_children(m)
					self._log.debug("Module %s updated state to %s ..." % (m.id, m.state))
					updated_instances.add(inst)

				#for inst in updated_instances:
				#	self._log.debug(repr(inst))

		except Exception:
			self._log.exception("Exception in wok-engine run thread")
		finally:
			self._lock.release()
			job_mgr.close()
			self._lock.acquire()

		try:
			# print instances state before leaving the thread
			for inst in self._instances:
				self._log.debug("Instances state:\n" + repr(inst))

			for t in self._logs_threads:
				t.join()

			self._join_thread.join()

			self._log.info("Engine run thread finished")
		except:
			pass

	def _logs(self):
		"Log retrieval thread"

		#_log = logger.get_logger(self.conf.get("wok.log"), "wok-engine")

		self._log.info("Engine logs thread ready")

		num_exc = 0

		while self._running:
			# get the next task to retrieve the logs
			job_info = self.__queue_adaptative_get(self._logs_queue)
			if job_info is None:
				continue

			task, job_id = job_info

			try:
				#TODO? self._lock.acquire()

				task.state_msg = "Reading logs"
				output = self._job_mgr.output(job_id)

				#TODO? self._lock.release()

				self._log.debug("Reading logs for task %s ..." % task.id)

				logs = []
				line = output.readline()
				while len(line) > 0:
					m = _LOG_RE.match(line)
					if m:
						timestamp = m.group(1) + " " + m.group(2)
						name = m.group(3)
						level = m.group(4).lower()
						text = m.group(5).decode("utf-8", "replace")
					else:
						timestamp = ""
						name = ""
						level = ""
						text = line.decode("utf-8", "replace")

					logs += [(timestamp, name, level, text)]

					line = output.readline()

					if len(line) == 0 or len(logs) >= 1000:
						self._lock.acquire()

						#TODO incorporate logs into the storage
						#self._storage.logs_append(instance_name, module_path, task_index, logs)

						self._log.debug("Task %s partial logs:\n%s" % (task.id, "\n".join("\t".join(log) for log in logs)))

						self._lock.release()

						logs = []
			except:
				num_exc += 1
				self._log.exception("Exception in wok-engine logs thread (%d)" % num_exc)

			finally:
				self._join_queue.put(job_info)

		self._log.info("Engine logs thread finished")

	def _join(self):
		"Joiner thread"

		self._log.info("Engine join thread ready")

		num_exc = 0

		while self._running:
			try:
				job_info = self.__queue_adaptative_get(self._join_queue)
				if job_info is None:
					continue

				task, job_id = job_info

				self._lock.acquire()

				task.job_result = self._job_mgr.join(job_id)
				del self._job_task_map[job_id]
				task.state_msg = ""

				self._log.debug("Task %s joined" % task.id)

				self._lock.release()

			except:
				num_exc += 1
				self._log.exception("Exception in wok-engine join thread (%d)" % num_exc)

		self._log.info("Engine join thread finished")

	@synchronized
	def start(self, wait = True):
		self._log.info("Starting engine ...")

		self._run_thread = Thread(target = self._run, name = "wok-engine-run")
		self._run_thread.start()

		if wait:
			self._lock.release()
			self.wait()
			self._lock.acquire()

	@synchronized
	def wait(self):
		self._log.info("Waiting for the engine ...")

		if self._run_thread is not None:
			self._lock.release()

			key_int = False
			while self._run_thread.isAlive():
				try:
					self._run_thread.join(1)
				except KeyboardInterrupt:
					with self._lock:
						if not key_int:
							self._log.warn("Ctrl-C pressed, stopping the engine ...")
							self._running = False
							key_int = True
						else:
							self._log.warn("Ctrl-C pressed, killing the process ...")
							import signal
							os.kill(os.getpid(), signal.SIGTERM)
				except Exception:
					with self._lock:
						self._log.exception("Exception while waiting for the engine to finish, stopping the engine ...")
						self._running = False

			self._lock.acquire()
			self._run_thread = None

	@synchronized
	def stop(self):
		self._log.info("Stopping the engine ...")

		self._running = False
		self._cvar.notify()

		self._lock.release()
		self.wait()
		self._lock.acquire()

	@synchronized
	def notify(self):
		self._notified = True
		self._cvar.notify()

	@synchronized
	def instance(self, name):
		inst = self._instances_map.get(name)
		if inst is None:
			return None
		return InstanceController(self, inst)
