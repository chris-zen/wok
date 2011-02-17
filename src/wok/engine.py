import os
import shutil
import sys
import math
import uuid
import json

from wok import logger
from wok.scheduler.factory import create_job_scheduler
from wok.portio.filedata import FileData
from wok.portio.pathdata import PathData
from wok.portio.multidata import MultiData
from wok.element import DataElement, DataElementJsonEncoder

class PortNode(object):
	def __init__(self, p_id, port, data = None):
		self.p_id = p_id
		self.port = port
		self.data = data

	def __str__(self):
		return self.p_id
		
	def __repr__(self):
		sb = [self.p_id]
		if self.data is not None:
			sb += [" <--> %s" % self.data]
		return "".join(sb)

class ModNode(object):
	def __init__(self, m_id, module):
		self.m_id = m_id
		self.module = module
		self.in_pnodes = None
		self.out_nodes = None
		self.scheduled = False

	def fill_element(self, e):
		e["id"] = self.m_id
		e["name"] = self.module.name
		return e
	
	def __str__(self):
		return self.m_id

	def __repr__(self):
		sb = [self.m_id]
		if self.in_pnodes is not None:
			sb += [" (%s)" % ",".join([str(x) for x in self.in_pnodes])]
		if self.out_pnodes is not None:
			sb += [" --> (%s)" % ",".join([str(x) for x in self.out_pnodes])]
		if self.scheduled:
			sb += [" [S]"]
		return "".join(sb)

def _map_add_list(m, k, v):
	if k not in m:
		m[k] = [v]
	else:
		m[k] += [v]

class WokEngine(object):
	def __init__(self, conf):
		self.conf = conf
		
		conf.check_required(["wok.bin_path", "wok.data_path"])

		wok_conf = conf["wok"]
		
		self._log = logger.get_logger(wok_conf, "wok")
		
		self._bin_path = wok_conf["bin_path"]
		self._data_path = wok_conf["data_path"]
		self._ports_path = os.path.join(self._data_path, "ports")
		self._tasks_path = os.path.join(self._data_path, "tasks")
		
		if "port_map" in wok_conf:
			self._port_data_conf = wok_conf["port_map"]
		else:
			self._port_data_conf = wok_conf.create_element()
		
		self._autorm_task = wok_conf.get("auto_remove.task", True, dtype=bool)

		self._clean = wok_conf.get("clean", True, dtype=bool)

		self._stop_on_errors = wok_conf.get("stop_on_errors", True, dtype=bool)

		self._mod_map = {}
		self._port_map = {}

		self._asc_dep = {} # {"child" : [parents]}
		#self._des_dep = {} # {"parent" : [children]} FIXME: Not used
		
		self._waiting = []
		self._finished = []

		self._job_sched = self._create_job_scheduler(wok_conf)

	def _create_job_scheduler(self, wok_conf):
		sched_name = wok_conf.get("scheduler", "default")

		sched_conf = wok_conf.create_element()
		if "schedulers.__default" in wok_conf:
			sched_conf.merge(wok_conf["schedulers.__default"])

		sched_conf_key = "schedulers.%s" % sched_name
		if sched_conf_key in wok_conf:
			sched_conf.merge(wok_conf[sched_conf_key])

		self._log.debug("Creating '%s' scheduler with configuration %s" % (sched_name, sched_conf))

		return create_job_scheduler(sched_name, sched_conf)

	def _ns_name(self, ns, name):
		if len(ns) == 0:
			return name
		else:
			return "%s.%s" % (ns, name)

	def _populate_flow(self, flow, ns = ""):
		self._log.debug("Analyzing flow ...")
		
		# populate modules
		for m in flow.modules:
			if m.enabled:
				m_id = self._ns_name(ns, m.name)
				mnode = ModNode(m_id, m)
				self._mod_map[m_id] = mnode
				self._waiting += [mnode]

		# populate ports
		self._populate_ports(flow.in_ports)
		self._populate_ports(flow.out_ports)

		for m_id, mnode in self._mod_map.iteritems():
			m = mnode.module
			mnode.in_pnodes = self._populate_ports(m.in_ports, m_id)
			mnode.out_pnodes = self._populate_ports(m.out_ports, m_id)

		self._connect_ports()

		#TODO: Check that there is no unattached input ports

	def _populate_ports(self, ports, ns = ""):
		pnodes = []
		for p in ports:
			p_id = self._ns_name(ns, p.name)
			pnode = PortNode(p_id, p)
			pnodes += [pnode]
			if p_id in self._port_map:
				sb = ["Duplicated port name '%s'" % p.name]
				if len(ns) > 0:
					sb += [" at '%s'" % ns]
				raise Exception("".join(sb))
			self._port_map[p_id] = pnode
		return pnodes

	def _connect_ports(self):
		# create ports data
		
		# first the ports which are source for others
		for p_id, pnode in self._port_map.iteritems():
			port = pnode.port
			if p_id in self._port_data_conf: # attached through user configuration
				port_data_conf = self._port_data_conf[p_id]
				if isinstance(port_data_conf, DataElement):
					raise Exception("Configurable attached port unimplemented")
				else: # By default we expect a file/dir path
					path = str(port_data_conf)
					if not os.path.exists(path):
						raise Exception("File not found: %s" % path)

					if os.path.isdir(path):
						pnode.data = PathData(path)
					elif os.path.isfile(path):
						pnode.data = FileData(path)
					else:
						raise Exception("Unexpected path type: %s" % path)
			elif len(port.src) == 0: # src not defined (they are source ports)
				rel_path = p_id.replace(".", "/")
				path = os.path.join(self._data_path, "ports", rel_path)
				if not os.path.exists(path):
					os.makedirs(path)
				pnode.data = PathData(path)

		# then the ports that link to source ports
		for p_id, pnode in self._port_map.iteritems():
			port = pnode.port
			if len(port.src) != 0:
				data = []
				for src in port.src:
					if src not in self._port_map:
						raise Exception("Port %s references a non-existent port: %s" % (p_id, src))
		
					src_port = self._port_map[src]
					data += [src_port.data.get_slice()]
				if len(data) == 1:
					pnode.data = data[0]
				else:
					pnode.data = MultiData(data)
				
		# check that there are no ports without data
		for p_id, pnode in self._port_map.iteritems():
			if pnode.data is None:
				raise Exception("Unconnected port: %s" % p_id)

	def _populate_dependencies(self, ns = ""):
		self._log.debug("Calculating dependencies ...")
		for m_id, mnode in self._mod_map.iteritems():
			m = mnode.module
			if len(m.depends) > 0:
				for dname in m.depends:
					d_id = self._ns_name(ns, dname)
					dm = self._mod_map[d_id]
					_map_add_list(self._asc_dep, m_id, dm)
					# TODO remove _map_add_list(self._des_dep, d_id, m)

			for p in m.in_ports:
				if len(p.src) == 0:
					continue

				for src in p.src:
					parts = src.split(".")
					if len(parts) <= 1:
						continue

					d_id = ".".join(parts[0:len(parts) - 1])
					if d_id not in self._mod_map:
						continue

					dm = self._mod_map[d_id]
					_map_add_list(self._asc_dep, m_id, dm)
					# TODO remove _map_add_list(self._des_dep, d_id, m)

	def _schedule_batch(self):
		batch = []
		for mnode in self._waiting:
			if mnode.m_id in self._asc_dep:
				select = True
				for dnode in self._asc_dep[mnode.m_id]:
					if not dnode.scheduled:
						select = False
						break
				if not select:
					continue

			batch += [mnode]
					
		for mnode in batch:
			mnode.scheduled = True
			self._waiting.remove(mnode)
	
		return batch
	
	def _create_task(self, conf, flow, mnode, t_id = None):
		task = DataElement(key_sep = "/")
		if t_id is not None:
			task["id"] = t_id
		task["flow"] = flow.name
		task["module"] = task_module = task.create_element()
		mnode.fill_element(task_module)
		task["conf"] = conf
		task["exec"] = task_exec = task.create_element()
		mnode.module.execution.fill_element(task_exec)
		task["ports"] = task.create_element()
		return task

	def _persist_task(self, task):
		path = os.path.join(self._data_path, "tasks")
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
	
	def _schedule_module(self, flow, mnode):
		# Calculate input sizes and the minimum depth
		psizes = []
		mdepth = sys.maxint
		for pnode in mnode.in_pnodes:
			psizes += [pnode.data.size()]
			port = pnode.port
			if port.depth < mdepth:
				mdepth = port.depth

		tasks = []
		
		if len(psizes) == 0:
			# Submit a task for the module without input ports information
			t_id = "%s-%04i" % (mnode.m_id, 0)
			task = self._create_task(self.conf, flow, mnode, t_id)
			tasks += [task]

			for pnode in mnode.out_pnodes:
				task_ports = task["ports"]
				e = task_ports.create_element()
				task_ports[pnode.port.name] = e
				data = pnode.data.get_slice(partition = pnode.data.last_partition)
				e["mode"] = "out"
				e["data"] = data.fill_element(e.create_element())
				pnode.data.last_partition += 1
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
				#TODO: Check mdepth == 0 --> some empty port
				num_partitions = int(math.ceil(psize / float(mdepth)))
				maxpar = mnode.module.maxpar
				if maxpar != -1:
					num_partitions = min(maxpar, num_partitions)
					if num_partitions == 0:
						mdepth = 0
					else:
						mdepth = int(math.ceil(psize / float(num_partitions)))
				self._log.debug("num_par=%i, psize=%i, mdepth=%i" % (num_partitions, psize, mdepth))

			start = 0
			partitions = []
			for i in xrange(num_partitions):
				t_id = "%s-%04i" % (mnode.m_id, i)
				task = self._create_task(self.conf, flow, mnode, t_id)
				tasks += [task]
				end = min(start + mdepth, psize)
				size = end - start
				partitions += [{"task" : task, "start" : start,  "size" : size}]
				self._log.debug("par=%i, start=%i, end=%i, size=%i" % (i, start, end, size))
				start += mdepth
				
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
					data = pnode.data.get_slice(start = partition["start"], size = size)
					e["mode"] = "in"
					e["data"] = data.fill_element(e.create_element())

			for pnode in mnode.out_pnodes:
				for partition in partitions:
					task = partition["task"]
					task_ports = task["ports"]
					e = task_ports.create_element()
					task_ports[pnode.port.name] = e
					data = pnode.data.get_slice(partition = pnode.data.last_partition)
					e["mode"] = "out"
					e["data"] = data.fill_element(e.create_element())
					pnode.data.last_partition += 1

		self._log.info("Running %i tasks for module '%s' ..." % (len(tasks), mnode))
		
		for task in tasks:
			self._persist_task(task)
			self._job_sched.submit(task)

		return tasks

	def run(self, flow):

		# Clean
		
		if self._clean:
			self._log.info("Cleaning ...")
			for path in [self._ports_path, self._tasks_path]:
				if os.path.exists(path):
					self._log.debug(path)
					shutil.rmtree(path)
				os.makedirs(path)

			self._job_sched.clean()

		# Initialize

		self._populate_flow(flow)
		self._populate_dependencies()
		
		sb = ["Modules input data:\n"]
		for m_id, mnode in self._mod_map.iteritems():
			sb += ["%s\n" % mnode]
			for pnode in mnode.in_pnodes:
				sb += ["\t%r\n" % pnode]
		self._log.debug("".join(sb))
		
		# Schedule batches
		
		self._log.info("Scheduling flow '%s' with %i modules ..." % (flow.name, len(self._mod_map)))
		
		batch_index = 0
		batch_modules = self._schedule_batch()
		while len(batch_modules) > 0:
			sb = ["Batch %i: " % batch_index]
			sb += [", ".join([str(x) for x in batch_modules])]
			self._log.info("".join(sb))

			tasks = []
			
			# Initializa ports data starting partition
			for mnode in batch_modules:
				for pnode in mnode.out_pnodes:
					pnode.data.start_partition = pnode.data.last_partition

			# Schedule modules in a batch
			for mnode in batch_modules:
				tasks += self._schedule_module(flow, mnode)

			# Wait for modules to finish
			self._job_sched.wait()

			# Update tasks and check failed ones
			failed = []
			for task in tasks:
				self._persist_task(task)

				job = task["job"]
				if "status" in job:
					status_code = job["status/code"]
					status_msg = job["status/msg"]
					if status_code != 0:
						failed += [task]
						sb = ["Task %s exited with code %i\n" % (task["id"], status_code)]
						# FIXME: Don't log output_path
						if "output_path" in job:
							output_path = job["output_path"]
							if os.path.exists(output_path):
								f = open(output_path, "r")
								sb += f.read()
								f.close()
						self._log.warn("".join(sb))
						
			if len(failed) > 0 and self._stop_on_errors:
				batch_modules = []
				continue

			if self._autorm_task:
				for task in tasks:
					os.remove(task["__doc_path"])
									
			self._finished += batch_modules
			batch_modules = self._schedule_batch()
			batch_index += 1

		if len(self._waiting) > 0:
			self._log.error("Flow finished before completing all modules")
		
		if len(failed) > 0:
			msg = "\n".join(["\t%s" % task["id"] for task in failed])
			self._log.error("Flow '%s' failed:\n%s" % (flow.name, msg))
		else:
			self._log.info("Flow '%s' finished successfully" % flow.name)

	def exit(self):
		self._job_sched.exit()

