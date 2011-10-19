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
from datetime import timedelta
import types

from wok import logger
from wok.config import Config
from wok.port import PortFactory, PORT_MODE_IN, PORT_MODE_OUT
from wok import exit_codes

class MissingRequiredPorts(Exception):
	def __init__(self, missing_ports, mode):
		Exception.__init__(self, "Missing required {0} ports: {1}".format(mode, ", ".join(missing_ports)))

class MissingRequiredConf(Exception):
	def __init__(self, missing_keys):
		Exception.__init__(self, "Missing required configuration: {0}".format(", ".join(missing_keys)))

class PortsAccessor(object):
	"""Port accessor for backward compatibility"""
	def __init__(self, ports):
		self.__ports = ports

	def __call__(self, *args, **kargs):
		if "mode" in kargs:
			mode = kargs["mode"]
		else:
			mode = [PORT_MODE_IN, PORT_MODE_OUT]

		if args is None or len(args) == 0:
			ports = [port for port in self.__ports.values() if port.mode in mode]
		else:
			names = []
			for arg in args:
				if isinstance(arg, list):
					names += arg
				else:
					names += [arg]

			try:
				ports = [self.__ports[name] for name in names]
			except Exception as e:
				raise Exception("Unknown port: {0}".format(e.args[0]))

		if len(ports) == 1:
			return ports[0]
		else:
			return tuple(ports)

	def keys(self):
		return self.__ports.keys()

	def __len__(self):
		return len(self.__ports)

	def __getitem__(self, key):
		return self.__ports[key]

	def __iter__(self):
		return iter(self.__ports)

	def __contains__(self, key):
		return key in self.__ports

	def items(self):
		return self.__ports.items()

	def iteritems(self):
		return self.__ports.iteritems()

class Task(object):
	"""
	Processes a data partition of a module in a flow.
	"""

	__DEFAULT_SERIALIZER = "json"
	
	def __init__(self, start_func = None, required_conf = []):

		# Read data and configuration
		self.data = Config(required = required_conf)
		self.conf = self.data["conf"]
		del self.data["conf"]

		self._id = self.data["id"]
		self.id = self._id
		self.index = self.data.get("index", -1, dtype = int)

		# deprecated
		self._start_func = start_func

		self._main = None
		self._generators = []
		self._foreach = None
		self._begin = None
		self._end = None

		self._start_time = 0
		self._end_time = self._start_time

		logger.initialize(self.conf.get("log"))
		self._log = self.logger()

		self.__initialize_ports()

		self.__ports_accessor = PortsAccessor(self._port_map)
		
		self.context = None
		
		#self._log.debug("Task:\nData: %s\nConfiguration: %s" % (self.data, self.conf))
	
	def __initialize_ports(self):
		self._port_map = {}
		if "ports" in self.data:
			for port_name, port_conf in self.data["ports"].iteritems():
				self._port_map[port_name] = PortFactory.create_port(port_name, port_conf)
		
	def __close_ports(self):
		for port in self._port_map.values():
			port.close()

	@staticmethod
	def __dot_product(ports):
		names = [port.name for port in ports]
		readers = [port.data.reader() for port in ports]
		sizes = [readers[i].size() for i in xrange(len(readers))]

		while sum(sizes) > 0:
			data = {}
			for i, reader in enumerate(readers):
				data[names[i]] = reader.read()
				sizes[i] = reader.size()
			yield data

	@staticmethod
	def __cross_product(ports):
		raise Exception("Cross product unimplemented")

	def __default_main(self):

		## Execute before main

		if self._begin:
			self._log.debug("Running task begin ...")
			self._begin()

		## Execute generators

		if self._generators:
			self._log.debug("Running task generators ...")

		for generator in self._generators:
			func, out_ports = generator

			self._log.debug("".join([func.__name__,
				"(out_ports=[", ", ".join([p.name for p in out_ports]), "])"]))

			params = [port for port in out_ports]

			func(*params)

		## Execute foreach's

		if self._foreach is not None:
			self._log.debug("Running [foreach] ...")

			# initialize foreach
			func, in_ports, out_ports = self._foreach

			writers = []
			writers_index = {}
			for i, port in enumerate(out_ports):
				writer = port.data.writer()
				writer.open()
				writers.append(writer)
				writers_index[port.name] = i

			self._log.debug("".join([func.__name__,
				"(in_ports=[", ", ".join([p.name for p in in_ports]),
				"], out_ports=[", ", ".join([p.name for p in out_ports]), "])"]))

			# determine input port data iteration strategy
			# currently only dot strategy supported
			iteration_strategy = self.__dot_product

			# process each port data iteration element
			for data in iteration_strategy(in_ports):

				params = [data[port.name] for port in in_ports]

				ret = func(*params)

				if ret is not None:
					if isinstance(ret, dict):
						for port_name, value in ret.items():
							index = writers_index[port_name]
							writers[index].write(value)
					else:
						if not isinstance(ret, (list, tuple)):
							ret = (ret,)

						if len(ret) != len(out_ports):
							port_list = ", ".join([p.name for p in out_ports])
							raise Exception("The number of values returned by '%s' doesn't match the expected output ports: [%s]" % (func.__name__, port_list))

						for i, writer in enumerate(writers):
							writer.write(ret[i])

			for writer in writers:
				writer.close()

		## Execute after main
		if self._end:
			self._log.debug("Running task end ...")
			self._end()

		return 0

	def elapsed_time(self):
		return timedelta(seconds = time.time() - self._start_time)

	def logger(self, name = None):
		if name is None:
			name = self._id
		log = logger.get_logger(self.conf.get("log"), name)
		return log

	# deprecated, use ports() instead
	def port(self, name):
		if name not in self._port_map:
			raise Exception("Port '{0}' doesn't exist".format(name))

		return self._port_map[name]

	@property
	def ports(self):
		return self.__ports_accessor

	def check_conf(self, keys, exit_on_error = True):
		missing_keys = []
		for key in keys:
			if key not in self.conf:
				missing_keys += [key]

		if exit_on_error and len(missing_keys) > 0:
			raise MissingRequiredConf(missing_keys)

		return missing_keys

	# deprecated
	def check_ports(self, port_names, mode, exit_on_error = True):
		missing_ports = []
		for port_name in port_names:
			if port_name not in self._port_map or self._port_map[port_name].mode != mode:
				missing_ports += [port_name]

		if exit_on_error and len(missing_ports) > 0:
			raise MissingRequiredPorts(missing_ports, mode)

		return missing_ports

	# deprecated
	def check_in_ports(self, port_names, exit_on_error = True):
		return self.check_ports(port_names, PORT_MODE_IN, exit_on_error)

	# deprecated
	def check_out_ports(self, port_names, exit_on_error = True):
		return self.check_ports(port_names, PORT_MODE_OUT, exit_on_error)

	def start(self):
		try:
			import socket
			hostname = socket.gethostname()
		except:
			hostname = "unknown"

		self._log.debug("Task {0} started on host {1}".format(self._id, hostname))

		self._start_time = time.time()

		try:
			if self._main is not None:
				self._log.debug("Running main ...")
				retcode = self._main()
				if retcode is None:
					retcode = 0
			elif self._start_func is not None:
				retcode = self._start_func(self)
				if retcode is None:
					retcode = 0
			else:
				retcode = self.__default_main()

			self._log.info("Elapsed time: {0}".format(self.elapsed_time()))
		except:
			self._log.exception("Exception on task {0}".format(self._id))
			retcode = exit_codes.TASK_EXCEPTION
		finally:
			self.__close_ports()

		exit(retcode)
		
	def set_main(self, f):
		self._main = f

	def main(self):
		"""
		A decorator that is used for specifying which is the task main function. Example::

			@task.main()
			def main():
				log = task.logger()
				log.info("Hello world")
		"""
		def decorator(f):
			self.set_main(f)
			return f

		return decorator

	def add_generator(self, generator_func, out_ports = None):
		"""Add a port data generator function"""
		if out_ports is None:
			ports = self.ports(mode = PORT_MODE_OUT)
		else:
			ports = self.ports(out_ports, mode = PORT_MODE_OUT)
		if not isinstance(ports, (tuple, list)):
			ports = (ports,)
		self._generators += [(generator_func, ports)]

	def generator(self, out_ports = None):
		"""
		A decorator that is used to define a function that will
		generate port output data. Example::

			@task.generator(out_ports = ["x", "sum"])
			def sum_n(x, sum):
				N = task.conf["N"]
				s = 0
				for i in xrange(N):
					x.write(i)
					sum.write(s)
					s += i
		"""
		def decorator(f):
			self.add_generator(f, out_ports)
			return f
		return decorator

	def set_foreach(self, foreach_func, in_ports = None, out_ports = None):
		"""Set the port data foreach function"""
		if in_ports is None:
			iports = self.ports(mode = PORT_MODE_IN)
		else:
			iports = self.ports(in_ports, mode = PORT_MODE_IN)
		if not isinstance(iports, (tuple, list)):
			iports = (iports,)
		if out_ports is None:
			oports = self.ports(mode = PORT_MODE_OUT)
		else:
			oports = self.ports(out_ports, mode = PORT_MODE_OUT)
		if not isinstance(oports, (tuple, list)):
			oports = (oports,)
		self._foreach = (foreach_func, iports, oports)

	def mapper(self, in_ports = None, out_ports = None):
		"""
		A decorator that is used to specify which is the function that will
		process each port input data. Example::

			@task.mapper(in_ports = ["in1", "in2"])
			def process(name, value):
				return name + " = " + str(value)
		"""
		def decorator(f):
			self.set_foreach(f, in_ports, out_ports)
			return f
		return decorator

	def foreach(self, in_ports = None, out_ports = None):
		"""
		A decorator that is used to specify which is the function that will
		process each port input data. Example::

			@task.mapper(in_ports = ["in1", "in2"])
			def process(name, value):
				return name + " = " + str(value)
		"""
		def decorator(f):
			self.set_foreach(f, in_ports, out_ports)
			return f
		return decorator

	def set_begin(self, f):
		"""Set the function that will be executed before starting the main function"""
		self._begin = f

	def begin(self):
		"""A decorator that is used to specify the function that will be
		executed before starting the main function"""
		def decorator(f):
			self.set_begin(f)
			return f
		return decorator

	def set_end(self, f):
		"""Set the function that will be executed before starting the main function"""
		self._end = f

	def end(self):
		"""A decorator that is used to specify the function that will be
		executed after executing the main function"""
		def decorator(f):
			self.set_end(f)
			return f
		return decorator

	def shell(self, cmd, env, success = None, **kwargs):
		sb = [cmd]
		if env is not None:
			for k in sorted(env):
				sb += ["\n\t", k, "=", env[k]]
		self._log.debug("".join(sb))

		exit_code, stats = monproc.call(cmd, env, **kwargs)

		sb = ["Exit code = ", str(exit_code)]
		for k in sorted(stats):
			sb += ["\n\t", k, " = ", stats[k]]
		self._log.debug("".join(sb))

		if success is not None:
			if success.__class__ is types.FunctionType:
				ok = success(exit_code)
			elif isinstance(success, list):
				ok = exit_code in success
			else:
				ok = exit_code == success

			if not ok:
				raise Exception("Shell command failed with exit code = %s" % exit_code)
		else:
			ok = True

		return (ok, exit_code, stats)
