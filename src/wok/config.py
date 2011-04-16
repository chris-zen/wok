import os.path
import json

from wok import __version__
from wok.element import DataElement, DataFactory

class Config(DataElement):
	"""
	Command line options parser and configuration loader.

	It parses the arguments, loads configuration files (with -c option)
	and appends new configuration parameters (with -D option)
	"""
	
	def __init__(self, required = [], args_usage = "", add_options = None, expand_vars = False):
		DataElement.__init__(self)
		
		from optparse import OptionParser

		parser = OptionParser(usage = "usage: %prog [options] " + args_usage, version = __version__)

		parser.add_option("-L", "--log-level", dest="log_level", 
			default=None, choices=["debug", "info", "warn", "error", "critical", "notset"],
			help="Which log level: debug, info, warn, error, critical, notset")

		parser.add_option("-c", "--conf", action="append", dest="conf_files", default=[], metavar="FILE",
			help="Load configuration from a file. Multiple files can be specified")
			
		parser.add_option("-D", action="append", dest="data", default=[], metavar="PARAM=VALUE",
			help="External data value. example -D param1=value")

		if add_options is not None:
			add_options(parser)

		(self.options, self.args) = parser.parse_args()

		if self.options.log_level is not None:
			self["wok.log.level"] = self.options.log_level

		if len(self.options.conf_files) > 0:
			base_path = "" #TODO current dir
			files = []
			for conf_file in self.options.conf_files:
				if os.path.isabs(conf_file):
					files.append(conf_file)
				else:
					files.append(os.path.join(base_path, conf_file))
				try:
					f = open(conf_file, "r")
					conf = DataFactory.from_native(json.load(f))
					self.merge(conf)
					f.close()
				except:
					from wok import logger
					log_conf = self.get("wok.log")
					logger.initialize(log_conf)
					logger.get_logger(log_conf, "config").error("Error reading configuration file: %s" % conf_file)
					raise

			self["__files"] = DataFactory.from_native(files)

		for data in self.options.data:
			d = data.split("=")
			if len(d) != 2:
				raise Exception("Data argument wrong: " + data)

			self[d[0]] = d[1]

		if len(required) > 0:
			self.check_required(required)

		if expand_vars:
			self.expand_vars()

	def check_required(self, required):
		for name in required:
			if not name in self:
				raise Exception("Missing required configuration: %s" % name)
