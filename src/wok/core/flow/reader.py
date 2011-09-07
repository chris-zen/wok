# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

import os.path

try:
	from lxml import etree
except ImportError:
	try:
		# Python 2.5
		import xml.etree.cElementTree as etree
	except ImportError:
		try:
			# Python 2.5+
			import xml.etree.ElementTree as etree
		except ImportError:
			try:
				# normal cElementTree install
				import cElementTree as etree
			except ImportError:
				try:
					# normal ElementTree install
					import elementtree.ElementTree as etree
				except ImportError:
					import sys
					sys.stderr.write("Failed to import ElementTree from any known place\n")
					raise

from wok.element import DataElement, dataelement_from_xml
from wok.core.flow.model import *

def str_to_bool(s):
	s2b = {
		"0" : False, "1" : True,
		"no" : False, "yes" : True,
		"false" : False, "true" : True}
	if s in s2b:
		return s2b[s]
	else:
		return False

class FlowReader(object):
	def __init__(self, source):
		if isinstance(source, str):
			self.path = os.path.abspath(source)
			self.fp = open(source, "r")
		else:
			self.path = None
			self.fp = source

		self.__doc = None

	def __read_doc(self):
		if self.__doc is None:
			self.__doc = etree.parse(self.fp)
		return self.__doc

	def read_meta(self):
		doc = self.__read_doc()
		root = doc.getroot()
		if root.tag != "flow":
			raise Exception("<flow> expected but <{}> found".format(xmle.tag))
		
		name = root.attrib.get("name")
		library = root.attrib.get("library")
		version = root.attrib.get("version")
		return (name, library, version)

	def read(self):
		doc = self.__read_doc()
		root = doc.getroot()
		flow = self._parse_flow(root)
		if self.path:
			flow.path = self.path
		return flow

	def _parse_base_desc(self, xmle, obj):
		if "name" not in xmle.attrib:
			raise Exception("'name' attribute not found in tag <{}>".format(xmle.tag))

		obj.name = xmle.attrib["name"]
		
		obj.title = xmle.findtext("title")
		obj.desc = xmle.findtext("desc")

		if "enabled" in xmle:
			obj.enabled = str_to_bool(xmle.attr["enabled"])
		
	def _parse_base_port(self, xmle, obj):
		self._parse_base_desc(xmle, obj)

		if "serializer" in xmle.attrib:
			obj.serializer = xmle.attrib["serializer"]

		if "wsize" in xmle.attrib:
			obj.wsize = xmle.attrib["wsize"]
			if obj.wsize < 1:
				raise Exception("At {} {}: 'wsize' should be a number greater than 0".format(xmle.tag, obj.name))

	def _parse_base_module(self, xmle, obj):
		self._parse_base_port(xmle, obj)

		if "maxpar" in xmle.attrib:
			obj.maxpar = int(xmle.attrib["maxpar"])
		
		conf_xml = xmle.find("conf")
		if conf_xml is not None:
			obj.conf = self._parse_conf(conf_xml)

		for x in xmle.findall("in"):
			obj.add_in_port(self._parse_port(x))
		
		for x in xmle.findall("out"):
			obj.add_out_port(self._parse_port(x))

	def _parse_flow(self, xmle):
		if xmle.tag != "flow":
			raise Exception("<flow> expected but <{}> found".format(xmle.tag))
		
		flow = Flow(name = None)
		self._parse_base_module(xmle, flow)

		if "library" in xmle.attrib:
			flow.library = xmle.attrib["library"]

		if "version" in xmle.attrib:
			flow.version = xmle.attrib["version"]

		for xmle in xmle.findall("module"):
			module = self._parse_module(flow, xmle)
			# TODO check that there is no other module with the same name
			flow.add_module(module)
		
		return flow
		
	def _parse_module(self, flow, xmle):
		mod = Module(name = None)

		self._parse_base_module(xmle, mod)

		if "depends" in xmle.attrib:
			depends = [d.strip() for d in xmle.attrib["depends"].split(",")]
			mod.depends = [d for d in depends if len(d) > 0]

		exec_xml = xmle.find("exec")
		if exec_xml is None:
			run_xml = xmle.find("run")
			if run_xml is None:
				flow_ref_xml = xmle.find("flow")
				if flow_ref_xml is None:
					raise Exception("Missing either <exec>, <run> or <flow> in module {}".format(mod.name))
				else:
					mod.flow_ref = self._parse_flow_ref(flow, mod, flow_ref_xml)
			else:
				mod.execution = self._parse_run(mod, run_xml)
		else:
			mod.execution = self._parse_exec(exec_xml)
		
		return mod

	def _parse_port(self, xmle):
		if xmle.tag == "in":
			mode = PORT_MODE_IN
		elif xmle.tag == "out":
			mode = PORT_MODE_OUT
		
		port = Port(name = None, mode = mode)

		self._parse_base_port(xmle, port)

		if "link" in xmle.attrib:
			link = [x.strip() for x in xmle.attrib["link"].split(",")]
			port.link = [l for l in link if len(l) > 0]

		return port

	def _parse_conf(self, xmle):
		return dataelement_from_xml(xmle)

	def _parse_exec(self, xmle):
		execution = Exec()
		
		if "launcher" in xmle.attrib:
			execution.mode = xmle.attrib["launcher"].lower()
			if execution.mode == "python":
				execution.mode = "native"

		execution.conf = dataelement_from_xml(xmle)

		return execution

	def _parse_run(self, mod, xmle):
		if xmle.text is None or len(xmle.text) == 0:
			raise Exception("Missing script name for <run> in module {}".format(mod.name))

		execution = Exec()
		execution.mode = "native"
		execution.conf = DataElement()
		execution.conf["script_path"] = xmle.text

		return execution

	def _parse_flow_ref(self, flow, mod, xmle):
		if xmle.text is None or len(xmle.text) == 0:
			raise Exception("Missing flow name for <flow> in module {}".format(mod.name))

		flow_ref = FlowRef()

		pos = xmle.text.rfind(".")
		if pos == -1 and flow.library is not None:
			flow_ref.canonical_name = "{}.{}".format(flow.library, xmle.text)
		else:
			flow_ref.canonical_name = xmle.text

		if "version" in xmle.attrib:
			flow_ref.version = xmle.attrib["version"]
		
		return flow_ref

	def close(self):
		self.fp.close()
