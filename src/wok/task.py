import time

from datetime import timedelta

from wok import logger
from wok.config import Config
from wok.port import PortFactory

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

		logger.initialize(self.conf)

		log = self.logger()
		log.debug("Task: %s\nConfiguration: %s" % (self.data, self.conf))
	
	def _start_timer(self):
		self._start_time = time.time()
		
	def logger(self, name = None):
		log = logger.get_logger(self.conf, name)
		return log

	def _initialize_ports(self):
		ports = {}
		if "ports" in self.data:
			for port_name, port_conf in self.data["ports"].iteritems():
				ports[port_name] = PortFactory.create_port(port_name, port_conf)
		return ports
		
	def _close_ports(self):
		for port_name, port in self.ports.iteritems():
			port.close()

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

	def run(self):
		return 0

	def elapsed_time(self):
		return timedelta(seconds = time.time() - self._start_time)

