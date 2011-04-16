import time

from datetime import timedelta

from wok import logger
from wok.config import Config
from wok.port import PortFactory

class MissingRequiredPorts(Exception):
	def __init__(self, missing_ports, mode):
		Exception.__init__(self, "Missing required %s ports: %s" % (mode, ", ".join(missing_ports)))

class MissingRequiredConf(Exception):
	def __init__(self, missing_keys):
		Exception.__init__(self, "Missing required configuration: %s" % (", ".join(missing_keys)))

class Task(object):
	"""
	Processes a data partition of a module in a flow.
	
	* Configuration parameters:

	- The ones needed by the logger
	"""
	
	def __init__(self, run_delegate = None, required_conf = []):

		# Read data and configuration
		self.data = Config(required = required_conf)
		self.conf = self.data["conf"]
		del self.data["conf"]

		self._run_delegate = run_delegate

		self._start_time = 0
		self._end_time = self._start_time

		self.ports = self._initialize_ports()

		logger.initialize(self.conf.get("log"))

		#log = self.logger()
		#log.debug("Task:\nData: %s\nConfiguration: %s" % (self.data, self.conf))
	
	def _start_timer(self):
		self._start_time = time.time()

	def _initialize_ports(self):
		ports = {}
		if "ports" in self.data:
			for port_name, port_conf in self.data["ports"].iteritems():
				ports[port_name] = PortFactory.create_port(port_name, port_conf)
		return ports
		
	def _close_ports(self):
		for port_name, port in self.ports.iteritems():
			port.close()

	def logger(self, name = None):
		if name is None and "id" in self.data:
			name = self.data["id"]
		log = logger.get_logger(self.conf.get("log"), name)
		return log

	def port(self, name):
		if name not in self.ports:
			raise Exception("Port '%s' doesn't exist" % name)

		return self.ports[name]
	
	def start(self):
		self._start_timer()

		try:		
			if self._run_delegate is not None:
				retcode = self._run_delegate(self)
				if retcode is None:
					retcode = 0
			else:
				retcode = self.run()
		except:
			id = self.data.get("id", "UNKNOWN")
			self.logger().exception("Exception on task %s" % id)
			retcode = -1
		finally:
			self._close_ports()
	
		exit(retcode)

	def check_conf(self, keys, exit_on_error = True):
		missing_keys = []
		for key in keys:
			if key not in self.conf:
				missing_keys += [key]

		if exit_on_error and len(missing_keys) > 0:
			raise MissingRequiredConf(missing_keys)

		return missing_keys

	def check_ports(self, port_names, mode, exit_on_error = True):
		missing_ports = []
		for port_name in port_names:
			if port_name not in self.ports or self.ports[port_name].mode() != mode:
				missing_ports += [port_name]

		if exit_on_error and len(missing_ports) > 0:
			raise MissingRequiredPorts(missing_ports, mode)

		return missing_ports

	def check_in_ports(self, port_names, exit_on_error = True):
		return self.check_ports(port_names, "in", exit_on_error)

	def check_out_ports(self, port_names, exit_on_error = True):
		return self.check_ports(port_names, "out", exit_on_error)
	
	def run(self):
		return 0

	def elapsed_time(self):
		return timedelta(seconds = time.time() - self._start_time)

