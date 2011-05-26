# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

import os
import shutil
import sys
import math
import uuid
import json
import os
import os.path

from threading import Thread, Lock

from wok import logger
from wok.scheduler.factory import create_job_scheduler
from wok.serializer import DEFAULT_SERIALIZER_NAME
from wok.portio.filedata import FileData
from wok.portio.pathdata import PathData
from wok.portio.multidata import MultiData
from wok.element import DataElement, DataFactory, DataElementJsonEncoder

class WokAlreadyRunningError(Exception):
	pass

class WokInvalidOperationForStatusError(Exception):
	def __init__(self, op, status):
		Exception.__init__(self, "Invalid operation '%s' for current status '%s'" % (op, status))

class WokUninitializedError(Exception):
	pass

class PortNode(object):
	def __init__(self, p_id, port, serializer = DEFAULT_SERIALIZER_NAME, data = None):
		self.p_id = p_id
		self.port = port
		self.serializer = serializer
		self.data = data

	def __str__(self):
		return self.p_id
		
	def __repr__(self):
		sb = [self.p_id]
		if self.serializer is not None:
			sb += [" [", self.serializer, "]"]
		if self.data is not None:
			sb += [" <--> %s" % self.data]
		return "".join(sb)

class ModNode(object):
	S_UNINITIALIZED = 'uninitialized'
	S_WAITING = 'waiting'
	S_READY = 'ready'
	S_SUBMITTED = 'submitted'
	S_FAILED = 'failed'
	S_FINISHED = 'finished'

	def __init__(self, m_id, module):
		self.m_id = m_id
		self.module = module
		self.state = self.S_UNINITIALIZED
		self.in_pnodes = None
		self.out_pnodes = None
		self.conf = DataElement()
		self.num_tasks = 0
		self.submitted_tasks = []
		self.finished_tasks = []
		self.failed_tasks = []

	def fill_element(self, e):
		e["id"] = self.m_id
		e["name"] = self.module.name
		#TODO create section 'module' with module information
		e["state"] = self.state
		#TODO in & out ports
		e["num_tasks"] = self.num_tasks
		e["submitted_tasks"] = self.submitted_tasks
		e["finished_tasks"] = self.finished_tasks
		e["failed_tasks"] = self.failed_tasks
		return e
	
	def __str__(self):
		return self.m_id

	def __repr__(self):
		sb = [self.m_id]
		if self.in_pnodes is not None:
			sb += [" (%s)" % ",".join([str(x) for x in self.in_pnodes])]
		if self.out_pnodes is not None:
			sb += [" --> (%s)" % ",".join([str(x) for x in self.out_pnodes])]
		sb += [" [%s]" % self.status]
		return "".join(sb)

def _map_add_list(m, k, v):
	if k not in m:
		m[k] = [v]
	else:
		m[k] += [v]

def synchronized(lock):
	""" Synchronization decorator. """

	def wrap(f):
		def new_function(*args, ** kw):
			from wok.logger import get_logger
			get_logger(None, "wok").debug("acquire %s" % f.__name__)
			lock.acquire()
			try:
				return f(*args, ** kw)
			finally:
				lock.release()
				get_logger(None, "wok").debug("release %s" % f.__name__)
		return new_function
	return wrap

class RunThread(Thread):
	def __init__(self, wok):
		Thread.__init__(self, name = "wok-engine-run")
		self.wok = wok

	def run(self):
		self.wok._run()

_engine_lock = Lock()

class WokEngine(object):
	"""
	The Wok engine manages the execution of a workflow.

	It is created from a configuration object and then the run() method
	is called with a workflow already loaded in memory. At the end the exit()
	method has to be called to release resources.
	"""

	S_UNINITIALIZED = 'uninitialized'
	S_READY = 'ready'
	S_PAUSED = 'paused'
	S_RUNNING = 'running'
	S_FINISHED = 'finished'
	S_FAILED = 'failed'
	S_EXCEPTION = 'exception'
	S_EXITING = 'exiting'
	S_EXITED = 'exited'

	def __init__(self, conf, flow = None):
		self.conf = conf
		
		wok_conf = conf["wok"]
		
		self._log = logger.get_logger(wok_conf.get("log"), "wok")

		self._instance_name = wok_conf["__instance.name"]
		
		self._work_path = wok_conf.get("work_path", os.path.join(os.getcwd(), "wok"))
		self._output_path = os.path.join(self._work_path, "output")
		self._ports_path = os.path.join(self._work_path, "ports")
		self._tasks_path = os.path.join(self._work_path, "tasks")
		
		if "port_map" in wok_conf:
			self._port_data_conf = wok_conf["port_map"]
		else:
			self._port_data_conf = wok_conf.create_element()
		
		self._autorm_task = wok_conf.get("auto_remove.task", False, dtype=bool)

		self._clean = wok_conf.get("clean", True, dtype=bool)

		self._stop_on_errors = wok_conf.get("stop_on_errors", True, dtype=bool)

		self._maxpar = wok_conf.get("defaults.maxpar", 0, dtype=int)

		self._wsize = wok_conf.get("defaults.wsize", 0, dtype=int)

		self._flow = None
		
		self._state = WokEngine.S_UNINITIALIZED

		self._run_thread = None

		self._job_sched = self._create_job_scheduler(wok_conf)

		self._run_lock = Lock()
		
		if flow is not None:
			self._initialize(flow)

	def _create_job_scheduler(self, wok_conf):
		sched_name = wok_conf.get("scheduler", "default")

		sched_conf = wok_conf.create_element()
		if "schedulers.default" in wok_conf:
			sched_conf.merge(wok_conf["schedulers.default"])

		sched_conf_key = "schedulers.%s" % sched_name
		if sched_conf_key in wok_conf:
			sched_conf.merge(wok_conf[sched_conf_key])

		if "__output_path" not in sched_conf:
			sched_conf["__output_path"] = self._output_path

		if "__work_path" not in sched_conf:
			sched_conf["__work_path"] = os.path.join(self._work_path, sched_name)

		self._log.debug("Creating '%s' scheduler with configuration %s" % (sched_name, sched_conf))

		return create_job_scheduler(sched_name, sched_conf)

	def _ns_name(self, ns, name):
		if len(ns) == 0:
			return name
		else:
			return "%s.%s" % (ns, name)

	def _create_graph(self, flow, ns = ""):
		self._log.debug("Analyzing flow ...")

		self._mnodes_by_flow = []

		# create module nodes
		for m in flow.modules:
			if m.enabled:
				m_id = self._ns_name(ns, m.name)
				mnode = ModNode(m_id, m)
				self._mod_map[m_id] = mnode
				self._mnodes_by_flow.append(mnode)

		# create port nodes
		self._create_port_nodes(flow.in_ports)
		self._create_port_nodes(flow.out_ports)

		for m_id, mnode in self._mod_map.iteritems():
			m = mnode.module
			mnode.in_pnodes = self._create_port_nodes(m.in_ports, m, m_id)
			mnode.out_pnodes = self._create_port_nodes(m.out_ports, m, m_id)

		self._connect_ports()

		self._calculate_dependencies()
		
	def _create_port_nodes(self, ports, module = None, ns = ""):
		pnodes = []
		for p in ports:
			# pnode id
			p_id = self._ns_name(ns, p.name)
			if p_id in self._port_map:
				sb = ["Duplicated port name '%s'" % p.name]
				if len(ns) > 0:
					sb += [" at '%s'" % ns]
				raise Exception("".join(sb))
			
			# serializer
			serializer = None #DEFAULT_SERIALIZER_NAME
			if module is not None and module.serializer is not None:
				serializer = module.serializer
			if p.serializer is not None:
				serializer = p.serializer

			pnode = PortNode(p_id, p, serializer)
			self._port_map[p_id] = pnode
			pnodes += [pnode]

		return pnodes

	def _connect_ports(self):
		# create ports data

		# first the ports which are source for others
		for p_id, pnode in self._port_map.iteritems():
			port = pnode.port
			if p_id in self._port_data_conf: # attached through user configuration
				pnode.port.link = [] # override flow specified connections
				port_data_conf = self._port_data_conf[p_id]
				if isinstance(port_data_conf, DataElement):
					raise Exception("Configurable attached port unimplemented")
				else: # By default we expect a file/dir path
					path = str(port_data_conf)
					if not os.path.exists(path):
						raise Exception("File not found: %s" % path)

					if os.path.isdir(path):
						pnode.data = PathData(pnode.serializer, path)
					elif os.path.isfile(path):
						pnode.data = FileData(pnode.serializer, path)
					else:
						raise Exception("Unexpected path type: %s" % path)
					
					pnode.serializer = DEFAULT_SERIALIZER_NAME

			elif len(port.link) == 0: # link not defined (they are source ports)
				rel_path = p_id.replace(".", "/")
				path = os.path.join(self._work_path, "ports", rel_path)
				if not os.path.exists(path):
					os.makedirs(path)
				pnode.data = PathData(pnode.serializer, path)

				if pnode.serializer is None:
					pnode.serializer = DEFAULT_SERIALIZER_NAME

		# then the ports that link to source ports
		for p_id, pnode in self._port_map.iteritems():
			port = pnode.port
			if len(port.link) != 0:
				data = []
				for link in port.link:
					if link not in self._port_map:
						raise Exception("Port %s references a non-existent port: %s" % (p_id, link))
		
					link_port = self._port_map[link]

					if pnode.serializer is not None and pnode.serializer != link_port.serializer:
						raise Exception("Unmatching serializer found while linking port '{0}' [{1}] with '{2}' [{3}]".format(pnode.p_id, pnode.serializer, link_port.p_id, link_port.serializer))

					data += [link_port.data.get_slice()]

				if len(data) == 1:
					pnode.data = data[0]
				else:
					pnode.data = MultiData(data)
				
		# check that there are no ports without data
		for p_id, pnode in self._port_map.iteritems():
			if pnode.data is None:
				raise Exception("Unconnected port: %s" % p_id)

	def _calculate_dependencies(self, ns = ""):
		self._log.debug("Calculating dependencies ...")
		for m_id, mnode in self._mod_map.iteritems():
			m = mnode.module
			if len(m.depends) > 0:
				for dname in m.depends:
					d_id = self._ns_name(ns, dname)
					dm = self._mod_map[d_id]
					_map_add_list(self._asc_dep, m_id, dm)
					# _map_add_list(self._des_dep, d_id, m)

			for p in m.in_ports:
				if len(p.link) == 0:
					continue

				for link in p.link:
					parts = link.split(".")
					if len(parts) <= 1:
						continue

					d_id = ".".join(parts[0:len(parts) - 1])
					if d_id not in self._mod_map:
						continue

					dm = self._mod_map[d_id]
					_map_add_list(self._asc_dep, m_id, dm)
					# _map_add_list(self._des_dep, d_id, m)

	def _mnodes_sorted_by_dependency(self):
		mnodes = list()
		ids = set()
		remaining = self._mnodes_by_flow

		while len(remaining) > 0:
			selected = []
			for mnode in remaining:
				if mnode.m_id in self._asc_dep:
					select = True
					for dnode in self._asc_dep[mnode.m_id]:
						if dnode.m_id not in ids:
							select = False
							break

					if not select:
						continue

				selected.append(mnode)

			for mnode in selected:
				remaining.remove(mnode)
				mnodes.append(mnode)
				ids.add(mnode.m_id)
		
		return mnodes

	def _next_batch(self):
		batch = []
		for mnode in self._waiting:
			if mnode.m_id in self._asc_dep:
				select = True
				for dnode in self._asc_dep[mnode.m_id]:
					if dnode.state != ModNode.S_FINISHED:
						select = False
						break

				if not select:
					continue

			batch += [mnode]
	
		return batch
	
	def _create_task(self, conf, flow, mnode, t_id = None):
		task = DataElement(key_sep = "/")
		if t_id is not None:
			task["id"] = t_id
		task["flow"] = flow.name
		#task["mnode"] = task_mnode = task.create_element()
		#mnode.fill_element(task_mnode)
		task["mnode"] = mnode.m_id
		task["conf"] = mnode.conf
		task["exec"] = task_exec = task.create_element()
		mnode.module.execution.fill_element(task_exec)
		task["ports"] = task.create_element()
		task["job"] = job = task.create_element()
		job["output_path"] = os.path.join(self._output_path, "%s.txt" % task["id"])
		return task

	def _persist_task(self, task):
		path = os.path.join(self._work_path, "tasks")
		if not os.path.exists(path):
			os.makedirs(path)
		if "id" not in task:
			task["id"] = str(uuid.uuid4())
		path = os.path.join(path, task["id"] + ".json")
		
		task["__doc_path"] = path
		
		#self._log.debug("Persisting task to %s ..." % path)
		f = open(path, "w")
		json.dump(task, f, sort_keys=True, indent=4, cls=DataElementJsonEncoder)
		f.close()

	def _load_task(self, t_id):
		path = os.path.join(self._work_path, "tasks", t_id + ".json")
		try:
			f = open(path, "r")
			task = DataFactory.from_native(json.load(f), key_sep = "/")
			f.close()
		except:
			self._log.error("Error reading task file: %s" % path)
			raise
		return task

	def _effective_wsize(self, wsize):
		if wsize == 0:
			wsize = max(self._wsize, 1)
		return wsize

	def _effective_maxpar(self, maxpar):
		if maxpar == 0:
			return self._maxpar
		elif self._maxpar == 0:
			return maxpar
		return min(self._maxpar, maxpar)

	def _schedule_tasks(self, flow, mnode):
		# Calculate input sizes and the minimum wsize
		psizes = []
		mwsize = sys.maxint
		for pnode in mnode.in_pnodes:
			psize = pnode.data.size()
			psizes += [psize]
			pwsize = self._effective_wsize(pnode.port.wsize)
			self._log.debug("{0}: size={1}, wsize={2}".format(pnode.p_id, psize, pwsize))
			if pwsize < mwsize:
				mwsize = pwsize

		tasks = []
		
		if len(psizes) == 0:
			# Submit a task for the module without input ports information
			#t_id = "%s-%04i" % (mnode.m_id, 0)
			t_id = mnode.m_id + "-0000"
			task = self._create_task(self.conf, flow, mnode, t_id)
			tasks += [task]

			for pnode in mnode.out_pnodes:
				task_ports = task["ports"]
				e = task_ports.create_element()
				task_ports[pnode.port.name] = e
				data = pnode.data.get_partition()
				e["mode"] = "out"
				e["data"] = data.fill_element(e.create_element())
		else:
			# Check whether all inputs have the same size
			psize = psizes[0]
			for i in xrange(1, len(psizes)):
				if psizes[i] != psize:
					psize = -1
					break
			
			# Partition the data on input ports
			if psize == -1:
				num_partitions = 1
				self._log.warn("Unable to partition a module with inputs of different size")
			else:
				if mwsize == 0:
					num_partitions = 1
					self._log.warn("Empty port, no partitioning")
				else:
					num_partitions = int(math.ceil(psize / float(mwsize)))
					maxpar = self._effective_maxpar(mnode.module.maxpar)
					self._log.debug("%s.maxpar=%i" % (mnode.module.name, maxpar))
					if maxpar > 0 and num_partitions > maxpar:
						num_partitions = maxpar
						mwsize = int(math.ceil(psize / float(num_partitions)))
					self._log.debug("num_par=%i, psize=%i, mwsize=%i" % (num_partitions, psize, mwsize))

			start = 0
			partitions = []
			for i in xrange(num_partitions):
				t_id = "%s-%04i" % (mnode.m_id, i)
				task = self._create_task(self.conf, flow, mnode, t_id)
				tasks += [task]
				end = min(start + mwsize, psize)
				size = end - start
				partitions += [{"task" : task, "start" : start,  "size" : size}]
				self._log.debug("par=%i, start=%i, end=%i, size=%i" % (i, start, end, size))
				start += mwsize
				
			#self._log.debug(repr(partitions))

			for pi in xrange(len(mnode.in_pnodes)):
				pnode = mnode.in_pnodes[pi]

				# TODO calculate seek positions
				
				for partition in partitions:
					task = partition["task"]
					task_ports = task["ports"]
					e = task_ports.create_element()
					task_ports[pnode.port.name] = e
					#if num_partitions == 1:
					#	size = psizes[pi]
					#else:
					#	size = partition["size"]
					data = pnode.data.get_slice(partition["start"], partition["size"])
					e["mode"] = "in"
					e["data"] = data.fill_element(e.create_element())

			for pnode in mnode.out_pnodes:
				for partition in partitions:
					task = partition["task"]
					task_ports = task["ports"]
					e = task_ports.create_element()
					task_ports[pnode.port.name] = e
					data = pnode.data.get_partition()
					e["mode"] = "out"
					e["data"] = data.fill_element(e.create_element())

		mnode.num_tasks = len(tasks)
		
		return tasks

	def clean(self):
		self._log.info("Cleaning ...")
		for path in [self._output_path, self._ports_path, self._tasks_path]:
			if os.path.exists(path):
				self._log.debug(path)
				shutil.rmtree(path)
			os.makedirs(path)
		self._job_sched.clean()

	def _initialize(self, flow):
		self._run_lock.acquire()

		self._flow = flow

		# Clean

		if self._clean:
			self.clean()

		# Initialize

		self._mod_map = {}
		self._port_map = {}

		self._asc_dep = {} # {"child" : [parents]}
		#self._des_dep = {} # {"parent" : [children]} FIXME: Not used

		self._waiting = []
		self._submitted = []
		self._finished = []
		self._failed = []

		self._create_graph(flow)

		self._mnodes_by_dep = self._mnodes_sorted_by_dependency()

		for mnode in self._mod_map.values():
			mnode.state = ModNode.S_WAITING
			self._waiting += [mnode]

			mnode.conf.merge(self.conf)
			if mnode.module.conf is not None:
				mnode.conf.merge(mnode.module.conf)

		sb = ["Modules ports mapping:\n"]
		for mnode in self._mnodes_by_dep:
			#sb += ["%s\n" % mnode]
			for pnode in mnode.in_pnodes:
				sb += ["\t", repr(pnode), "\n"]
		self._log.debug("".join(sb))

		self._state = WokEngine.S_READY

		self._run_lock.release()

	def _run(self):
		self._run_lock.acquire()

		self._state = WokEngine.S_RUNNING

		self._log.info("Running instance '%s' ..." % self._instance_name)
		self._log.info("Scheduling flow '%s' with %i modules ..." % (self._flow.name, len(self._mod_map)))

		try:
			# check that the output path exists
			if not os.path.exists(self._output_path):
				os.makedirs(self._output_path)

			batch_index = 0
			batch_modules = self._next_batch()
			while len(batch_modules) > 0:
				sb = ["Batch %i: " % batch_index]
				sb += [", ".join([str(x) for x in batch_modules])]
				self._log.info("".join(sb))

				tasks = []

				# Initialize ports data starting partition
				"""for mnode in batch_modules:
					for pnode in mnode.out_pnodes:
						pnode.data.reset()"""

				# Submit tasks
				for mnode in batch_modules:
					self._waiting.remove(mnode)
					self._submitted.append(mnode)
					mnode.state = ModNode.S_SUBMITTED
					mtasks = self._schedule_tasks(self._flow, mnode)

					self._log.info("Submitting %i tasks for module '%s' ..." % (len(mtasks), mnode))
					for task in mtasks:
						self._persist_task(task)
						self._job_sched.submit(task)
						mnode.submitted_tasks.append(task["id"])

					tasks += mtasks

				# Wait for modules to finish
				self._log.info("Waitting for the %i tasks to finish ..." % len(tasks))
				self._run_lock.release()
				self._job_sched.wait()
				self._run_lock.acquire()

				# Update tasks and check failed ones

				failed_tasks = []
				
				for task in tasks:
					self._persist_task(task)

					failed = False

					task_id = task["id"]

					mnode = self._mod_map[task["mnode"]]

					job = task["job"]
					if "exit" in job:
						exit_code = job["exit/code"]
						exit_message = job["exit/message"]
						exit_exception = job.get("exit/exception", None)
						if exit_code != 0:
							failed = True
							failed_tasks += [task]
							sb = ["Task %s failed with code %i\n" % (task["id"], exit_code)]
							#TODO print exception trace if exit_exception is not None

							self._log.error(exit_message)
							if exit_exception is not None:
								self._log.error(exit_exception)
						else:
							self._log.debug(exit_message)
							if exit_exception is not None:
								self._log.error(exit_exception)

					mnode.submitted_tasks.remove(task_id)
					if failed:
						mnode.failed_tasks.append(task_id)
					else:
						mnode.finished_tasks.append(task_id)

				for mnode in batch_modules:
					self._submitted.remove(mnode)
					if len(mnode.failed_tasks) > 0:
						mnode.state = ModNode.S_FAILED
						self._failed += [mnode]
					else:
						mnode.state = ModNode.S_FINISHED
						self._finished += [mnode]

				if len(failed_tasks) > 0 and self._stop_on_errors:
					break

				if self._autorm_task:
					for task in tasks:
						os.remove(task["__doc_path"])

				batch_modules = self._next_batch()
				batch_index += 1

			if len(self._waiting) > 0:
				self._log.error("Flow finished before completing all modules")

			if len(failed_tasks) > 0:
				msg = "\n".join(["\t%s" % task["id"] for task in failed_tasks])
				self._log.error("Flow '%s' failed:\n%s" % (self._flow.name, msg))
				self._state = WokEngine.S_FAILED
			else:
				self._log.info("Flow '%s' finished successfully" % self._flow.name)
				self._state = WokEngine.S_FINISHED

		except:
			self._state = WokEngine.S_EXCEPTION
			raise
		finally:
			self._run_lock.acquire(False)
			self._run_lock.release()

	def _stop(self):
		pass
	
	@synchronized(_engine_lock)
	def initialize(self, flow):
		self._initialize(flow)

	@synchronized(_engine_lock)
	def initialized(self):
		return self._state != WokEngine.S_UNINITIALIZED

	@synchronized(_engine_lock)
	def start(self, async = True):
		if self._state == WokEngine.S_RUNNING:
			raise WokAlreadyRunningError()

		if self._state not in [WokEngine.S_READY, WokEngine.S_PAUSED, WokEngine.S_FINISHED, WokEngine.S_FAILED, WokEngine.S_EXCEPTION]:
			raise WokInvalidOperationForStatusError('start', self._state)

		if self._state in [WokEngine.S_FINISHED, WokEngine.S_FAILED, WokEngine.S_EXCEPTION]:
			self._initialize(self._flow);

		self._run_thread = RunThread(self)
		self._run_thread.start()

		if not async:
			_engine_lock.release()
			self.wait()
			_engine_lock.acquire()

	@synchronized(_engine_lock)
	def pause(self):
		pass

	@synchronized(_engine_lock)
	def cont(self):
		pass

	@synchronized(_engine_lock)
	def stop(self):
		self._stop()

	@synchronized(_engine_lock)
	def wait(self):
		if self._run_thread is not None:
			self._run_thread.join()
			self._run_thread = None

	@synchronized(_engine_lock)
	def exit(self):
		self._stop()

		self._state = WokEngine.S_EXITING
		self._job_sched.exit()
		self._state = WokEngine.S_EXITED

	@synchronized(_engine_lock)
	def state(self):
		s = {}
		s["name"] = self._state
		s["title"] = self._state

		s["instance"] = self._instance_name

		s["mnodes"] = mnodes = {}
		for mnode in self._mod_map.itervalues():
			mnodes[mnode.m_id] = mnode.fill_element(DataElement()).to_native()

		s["mnodes_by_dep"] = [mnode.m_id for mnode in self._mnodes_by_dep]

		return s

	@synchronized(_engine_lock)
	def mnode_state(self, m_id):
		if m_id not in self._mod_map:
			return None

		mnode = self._mod_map[m_id]
		return mnode.fill_element(DataElement()).to_native()

	@synchronized(_engine_lock)
	def task_state(self, task_id):
		task = self._load_task(task_id)
		return task

	@synchronized(_engine_lock)
	def task_conf(self, task_id):
		task = self._load_task(task_id)
		return task["conf"]

	@synchronized(_engine_lock)
	def task_output(self, task_id):
		task = self._load_task(task_id)
		if task is None:
			return None

		output_path = task["job/output_path"]
		if not os.path.exists(output_path):
			return None

		f = open(output_path, "r")
		try:
			output = f.read()
			return output
		finally:
			f.close()

	@synchronized(_engine_lock)
	def module_conf(self, m_id):
		if m_id not in self._mod_map:
			return DataElement(key_sep = "/")

		mnode = self._mod_map[m_id]
		return mnode.conf

	@synchronized(_engine_lock)
	def module_output(self, m_id):
		if m_id not in self._mod_map:
			return ""

		mnode = self._mod_map[m_id]
		task_ids = mnode.submitted_tasks + mnode.finished_tasks + mnode.failed_tasks
		sb = []
		for task_id in sorted(task_ids):
			sb += ["\n==[ ", task_id, " ]", "=" * (74 - len(task_id)), "\n\n"]
			task = self._load_task(task_id)
			if task is None:
				continue

			output_path = task["job/output_path"]
			if not os.path.exists(output_path):
				continue

			f = open(output_path, "r")
			try:
				output = f.read()
				sb += [output]
			finally:
				f.close()

		return "".join(sb)
