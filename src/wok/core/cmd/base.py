# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

class CmdBuilder(object):
	def __init__(self, conf):
		self.conf = conf

	def prepare(self, task):
		raise Exception("Unimplemented")