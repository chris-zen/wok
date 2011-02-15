
from wok.element import dataelement_from_xml
from wok.model import *

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
	def __init__(self, path):
		if isinstance(path, str):
			self.fp = open(path, "r")
		else:
			self.fp = path
	
	def read(self):
		from lxml import etree
		doc = etree.parse(self.fp)
		root = doc.getroot()		
		flow = self.parse_flow(root)
		return flow
		
	def parse_flow(self, root):
		if root.tag != "flow":
			raise Exception("<flow> tag not found")
			
		if "name" not in root.attrib:
			raise Exception("'name' attribute not found for tag <flow>")
		
		name = root.attrib["name"]
		
		title = root.findall("title")
		if len(title) == 0:
			title = name
		elif len(title) == 1:
			title = title[0].text
		elif len(title) > 1:
			raise Exception("More than one <title> found")
		
		flow = Flow(name = name, title = title)
		
		for e in root.xpath("in"):
			flow.add_in_port(self.parse_port(e))
		
		for e in root.xpath("out"):
			flow.add_out_port(self.parse_port(e))

		for e in root.xpath("module"):
			flow.add_module(self.parse_module(e))
		
		return flow
		
	def parse_port(self, e):
		attr = e.attrib
		
		if "name" not in attr:
			raise Exception("'name' attribute not found for tag <%s>" % e.tag)
		
		if e.tag == "in":
			ptype = PORT_TYPE_IN
		elif e.tag == "out":
			ptype = PORT_TYPE_OUT
		else:
			raise Exception("Unexpected port type: %s" % e.tag)
			
		port = Port(name = attr["name"], ptype = ptype)
		
		if "src" in attr:
			src = [x.strip() for x in e.attrib["src"].split(",")]
			if len(src) != 1 or len(src[0]) != 0:
				port.src = src
		
		if "depth" in attr:
			port.depth = int(attr["depth"])
			if port.depth < 1:
				raise Exception("At port %s: 'depth' should be a number greater than 0" % port.name)

		return port

	def parse_module(self, e):
		attr = e.attrib
		
		if "name" not in attr:
			raise Exception("'name' attribute not found for tag <%s>" % e.tag)
		
		mod = Module(name = attr["name"])
		
		if "maxpar" in attr:
			mod.maxpar = int(attr["maxpar"])
			if mod.maxpar < 1:
				raise Exception("'maxpar' should be an integer greater or equal to 1 for module %s" % mod.name)

		if "enabled" in attr:
			mod.enabled = str_to_bool(attr["enabled"])

		if "depends" in attr:
			depends = attr["depends"].split(",")
			if len(depends) != 1 or len(depends[0]) != 0:
				mod.depends = depends

		for ep in e.xpath("in"):
			mod.add_in_port(self.parse_port(ep))
		
		for ep in e.xpath("out"):
			mod.add_out_port(self.parse_port(ep))
			
		el = e.xpath("exec")
		if len(el) == 0:
			raise Exception("Missing <exec> in module %s" % mod.name)
		elif len(el) == 1:
			mod.execution = self.parse_exec(el[0])
		elif len(el) > 1:
			raise Exception("More than one <exec> found in module %s" % mod.name)

		return mod

	def parse_exec(self, e):
		attr = e.attrib
		
		execution = Exec()
		
		if "launcher" in attr:
			execution.launcher = attr["launcher"]

		execution.conf = dataelement_from_xml(e)

		return execution

	def close(self):
		self.fp.close()
