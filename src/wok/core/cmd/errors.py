# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

class UnknownCmdBuilder(Exception):
	def __init__(self, name):
		Exception.__init__(self, "Unknown command builder: {}".format(name))

class MissingRequiredOption(Exception):
	def __init__(self, name):
		Exception.__init__(self, "Missing required option: {}".format(name))