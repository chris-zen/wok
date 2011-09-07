# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

import os
import os.path

import time
import shutil
import sys
import math
import uuid
import json

from threading import Thread, Lock, Condition

from wok import logger
from wok.element import DataElement, DataList, DataFactory, DataElementJsonEncoder
from wok.config import ConfigBuilder
from wok.core import runstates
from wok.core.flow.loader import FlowLoader
from wok.core.instance import Instance
from wok.core.jobmgr.factory import create_job_manager

def _map_add_list(m, k, v):
	if k not in m:
		m[k] = [v]
	else:
		m[k] += [v]

def synchronized(f):
	"""WokEngine synchronization decorator."""
	def wrap(f):
		def sync_function(engine, *args, **kw):
			#engine._log.debug("<ACQUIRE %s>" % f.__name__)
			engine._lock.acquire()
			try:
				return f(engine, *args, ** kw)
			finally:
				engine._lock.release()
				#engine._log.debug("<RELEASE %s>" % f.__name__)
		return sync_function
	return wrap(f)

class WokEngine(object):
	"""
	The Wok engine manages the execution of a workflow.

	It is created from a configuration object and then the run() method
	is called with a workflow already loaded in memory. At the end the exit()
	method has to be called to release resources.
	"""

	def __init__(self, conf):
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

		self._lock = Lock()
		self._cvar = Condition(self._lock)
		
		self._run_thread = None
		self._running = False
		
		self._notified = False

		self._job_mgr = self._create_job_manager(wok_conf)

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

	@property
	def flow_loader(self):
		return self._flow_loader

	@synchronized
	def create_instance(self, inst_name, conf_builder, flow_file):
		"Creates a new workflow instance"

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
		except:
			self._log.error("Error while creating instance {} for the workflow {} with configuration {}".format(inst_name, flow_file, cb()))
			raise

		self._log.debug("\n" + repr(inst))

		return inst

	@synchronized
	def _run(self):
		self._running = True

		job_mgr = self._job_mgr

		try:
			job_mgr.start()

			job_task_map = {}

			while self._running:

				self._log.debug("Scheduling new tasks ...")

				# submit tasks ready to be executed
				for inst in self._instances:
					tasks = inst.schedule_tasks()
					if len(tasks) > 0:
						#self._log.debug("ready_tasks:\n" + "\n".join(["\t" + t.id for t in tasks]))
						job_ids = job_mgr.submit(tasks)
						for i, task in enumerate(tasks):
							job_task_map[job_ids[i]] = task
							task.job_id = job_ids[i]
				
				self._log.debug("Waiting for events ...")

				while not self._notified and self._running:
					self._cvar.wait(2)
				self._notified = False

				if not self._running:
					break

				# set of modules which state has been affected by jobs state
				updated_modules = set()

				job_states = job_mgr.state()
				
				#self._log.debug("Job states:\n" + "\n".join("\t{}: {}".format(jid, jst) for jid, jst in job_states))

				for job_id, state in job_states:
					task = job_task_map[job_id]
					if task.state != state:
						task.state = state
						updated_modules.add(task.parent)

						if state in [runstates.FINISHED, runstates.FAILED]:
							task.job_result = job_mgr.join(job_id)
							del job_task_map[job_id]

				#self._log.debug("Updating modules state ...\n" + "\n".join("\t{}".format(m.id) for m in sorted(updated_modules)))
				self._log.debug("Updating modules state ...")

				# update affected modules state
				updated_instances = set()
				for m in updated_modules:
					inst = m.instance
					inst.update_module_state_from_children(m)
					updated_instances.add(inst)

				#for inst in updated_instances:
				#	self._log.debug(repr(inst))

			# print instances state before leaving the thread
			for inst in self._instances:
				self._log.debug(repr(inst))

		except Exception:
			self._log.exception("Exception in wok-engine run thread")
		finally:
			job_mgr.stop()

	@synchronized
	def start(self, async = True):
		self._log.info("Starting engine ...")
		
		self._run_thread = Thread(target = self._run, name = "wok-engine-run")
		self._run_thread.start()

		if not async:
			self._lock.release()
			self.wait()
			self._lock.acquire()

	@synchronized
	def wait(self):
		self._log.info("Waiting for the engine ...")

		if self._run_thread is not None:
			self._lock.release()

			while self._run_thread.isAlive():
				try:
					self._run_thread.join(1)
				except KeyboardInterrupt:
					with self._lock:
						self._log.warn("Ctrl-C pressed, stopping the engine ...")
						self._running = False
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
