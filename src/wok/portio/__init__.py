class PortData(object):
	def __init__(self, conf = None):
		pass

	def size(self):
		raise Exception("Unimplemented")
		
	def get_slice(self, partition = None, start = None, size = None):
		raise Exception("Unimplemented")

	def fill_element(self, e):
		raise Exception("Unimplemented")
		
	def reader(self):
		raise Exception("Unimplemented")
		
	def writer(self):
		raise Exception("Unimplemented")
