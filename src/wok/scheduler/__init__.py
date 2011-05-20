# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

class JobScheduler(object):

	def __init__(self, conf):
		self.conf = conf
	
	def clean(self):
		raise Exception("Unimplemented")

	def submit(self, task):
		raise Exception("Unimplemented")
	
	def exit(self):
		raise Exception("Unimplemented")
