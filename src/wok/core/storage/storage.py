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

from wok import logger
from wok.element import DataElement

class Storage(object):
	"""
	Abstract Storage interface.
	An Storage implementation manages any piece of information that should be shared between controller and execution nodes.
	"""

	def __init__(self, context, conf, name):
		self.context = context
		self.conf = conf
		self.name = name

		self._log = logger.get_logger(conf.get("log"), name)

	@staticmethod
	def _task_config_to_element(task):
		e = DataElement(key_sep = "/")
		e["id"] = task.id
		e["name"] = task.name
		e["index"] = task.index
		e["module"] = task.parent.id
		e["instance"] = task.instance.name
		e["conf"] = task.conf

		#TODO depends on module definition
		iter = e.create_element("iteration")
		iter["strategy"] = "dot"
		iter["size"] = 0
		
		ports = e.create_element("ports")

		in_ports = ports.create_list("in")
		for i, port_node in enumerate(task.parent.in_ports):
			pe = DataElement(key_sep = "/")
#			pe["name"] = port_node.name
#			pe["serializer"] = port_node.serializer
#			pe["partition"] = pdata.partition
#			pe["start"] = pdata.start
#			pe["size"] = pdata.size
			#task.in_port_data[i].fill_element(pe.create_element("data"))
			task.in_port_data[i].fill_element(pe)
			in_ports.append(pe)
			
		out_ports = ports.create_list("out")
		for i, port_node in enumerate(task.parent.out_ports):
			pe = DataElement(key_sep = "/")
#			pe["name"] = port_node.name
#			pe["serializer"] = port_node.serializer
#			pe["partition"] = pdata.partition
			#task.out_port_data[i].fill_element(pe.create_element("data"))
			task.out_port_data[i].fill_element(pe)
			out_ports.append(pe)
		
		return e

class StorageContext(object):
	"An enumeration for the different storage contexts available"

	CONTROLLER = 1
	EXECUTION = 2
