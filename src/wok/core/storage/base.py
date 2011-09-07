# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.element import DataElement

class Storage(object):
	def __init__(self, wok_conf):
		self.wok_conf = wok_conf

	@staticmethod
	def _task_to_element(task):
		e = DataElement(key_sep = "/")
		e["id"] = task.id
		e["name"] = task.name
		e["index"] = task.index
		e["module"] = task.parent.id
		e["instance"] = task.instance.name
		e["conf"] = task.conf

		ports = e.create_element("ports")
		ports["iteration_strategy"] = "dot" #TODO depends on module

		in_ports = ports.create_list("input")
		for i, port_node in enumerate(task.parent.in_ports):
			pe = DataElement(key_sep = "/")
			pe["name"] = port_node.name
			task.in_port_data[i].fill_element(pe.create_element("data"))
			in_ports.append(pe)
			
		out_ports = ports.create_list("output")
		for i, port_node in enumerate(task.parent.out_ports):
			pe = DataElement(key_sep = "/")
			pe["name"] = port_node.name
			task.out_port_data[i].fill_element(pe.create_element("data"))
			out_ports.append(pe)
		
		return e

	@staticmethod
	def _element_to_task():
		pass

class StorageContext(object):
	SERVER = 1
	EXECUTION = 2