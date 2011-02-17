import json

from wok import __version__
from wok.element import DataElement, DataFactory

class Config(DataElement):
	def __init__(self, required = [], args_usage = "", add_options = None, expand_vars = False):
		DataElement.__init__(self)
		
		from optparse import OptionParser

		parser = OptionParser(usage = "usage: %prog [options] " + args_usage, version = __version__)

		parser.add_option("-L", "--log-level", dest="log_level", 
			default="info", choices=["debug", "info", "warn", "error", "critical", "notset"], 
			help="Which log level: debug, info, warn, error, critical, notset")

		parser.add_option("-c", "--conf", action="append", dest="conf_files", default=[], metavar="FILE",
			help="Load configuration from a file. Multiple files can be specified")
			
		parser.add_option("-D", action="append", dest="data", default=[], metavar="PARAM=VALUE",
			help="External data value. example -D param1=value")

		if add_options is not None:
			add_options(parser)

		(self.options, self.args) = parser.parse_args()

		self["log.level"] = self.options.log_level

		if len(self.options.conf_files) > 0:
			for conf_file in self.options.conf_files:
				f = open(conf_file, "r")
				conf = DataFactory.from_native(json.load(f))
				self.merge(conf)
				f.close()
		
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
