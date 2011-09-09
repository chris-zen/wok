# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

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

		ports = e.create_element("ports")
		
		#TODO depends on module definition
		iter = ports.create_element("iteration")
		iter["strategy"] = "dot"
		iter["size"] = 0

		in_ports = ports.create_list("in")
		for i, port_node in enumerate(task.parent.in_ports):
			pe = DataElement(key_sep = "/")
			pe["name"] = port_node.name
			task.in_port_data[i].fill_element(pe.create_element("data"))
			in_ports.append(pe)
			
		out_ports = ports.create_list("out")
		for i, port_node in enumerate(task.parent.out_ports):
			pe = DataElement(key_sep = "/")
			pe["name"] = port_node.name
			task.out_port_data[i].fill_element(pe.create_element("data"))
			out_ports.append(pe)
		
		return e

class StorageContext(object):
	"An enumeration for the different storage context availables"

	CONTROLLER = 1
	EXECUTION = 2
