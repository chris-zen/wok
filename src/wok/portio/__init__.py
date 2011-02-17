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


class DataReader(object):
	def next(self):
		raise Exception("Unimplemented")

	def __iter__(self):
		return self

	def size(self):
		return self._size

	def read(self, size = 1):
		data = []
		if self.size() == 0:
			return None

		if not self.is_opened():
			self._open()

		try:
			while size > 0:
				data += [self.next()]
				size -= 1
		except StopIteration:
			pass

		if len(data) == 0:
			return None
		elif len(data) == 1:
			return data[0]
		else:
			return data
