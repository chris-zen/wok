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

import os.path
import json

from wok import __version__
from wok.element import DataElement, DataFactory

class ConfigFile(object):
	def __init__(self, path):
		self.path = os.path.abspath(path)

	def merge_into(self, conf):
		f = open(self.path, "r")
		v = json.load(f)
		cf = DataFactory.from_native(v)
		conf.merge(cf)
		f.close()

class ConfigValue(object):
	def __init__(self, key, value):
		self.key = key
		self.value = value

	def merge_into(self, conf):
		try:
			v = json.loads(self.value)
		except:
			v = self.value
		conf[self.key] = DataFactory.from_native(v)

class ConfigElement(object):
	def __init__(self, element):
		self.element = element

	def merge_into(self, conf):
		conf.merge(self.element)

class ConfigBuilder(object):
	def __init__(self):
		self.__parts = []

	def add_file(self, path):
		self.__parts += [ConfigFile(path)]

	def add_value(self, key, value):
		self.__parts += [ConfigValue(key, value)]

	def add_element(self, element):
		self.__parts += [ConfigElement(element)]

	def add_builder(self, builder):
		self.__parts += [builder]

	def merge_into(self, conf):
		for part in self.__parts:
			part.merge_into(conf)

	def get_conf(self, conf = None):
		if conf is None:
			conf = DataElement()
		self.merge_into(conf)
		return conf

	def __call__(self, conf = None):
		return self.get_conf(conf)

class OptionsConfig(DataElement):
	"""
	Command line options parser and configuration loader.

	It parses the arguments, loads configuration files (with -c option)
	and appends new configuration parameters (with -D option)
	"""
	
	def __init__(self, initial_conf = None, required = [], args_usage = "", add_options = None, expand_vars = False):
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

		self.builder = ConfigBuilder()

		if initial_conf is not None:
			if isinstance(initial_conf, dict):
				initial_conf = DataFactory.from_native(initial_conf)
			self.builder.add_element(initial_conf)

		if self.options.log_level is not None:
			self.builder.add_value("wok.log.level", self.options.log_level)

		if len(self.options.conf_files) > 0:
			files = []
			for conf_file in self.options.conf_files:
				self.builder.add_file(conf_file)
				files.append(os.path.abspath(conf_file))

			self.builder.add_value("__files", DataFactory.from_native(files))

		for data in self.options.data:
			d = data.split("=")
			if len(d) != 2:
				raise Exception("Data argument wrong: " + data)

			self.builder.add_value(d[0], d[1])

		self.builder.merge_into(self)

		if len(required) > 0:
			self.check_required(required)

		if expand_vars:
			self.expand_vars()

	def check_required(self, required):
		for name in required:
			if not name in self:
				raise Exception("Missing required configuration: %s" % name)
