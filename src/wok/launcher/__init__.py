# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************


class Launcher(object):

	def __init__(self, conf):
		self.conf = conf

	def template(self, exec_conf, task):
		raise Exception("Unimplemented")
