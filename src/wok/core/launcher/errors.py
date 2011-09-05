# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

class UnknownLauncher(Exception):
	def __init__(self, name):
		Exception.__init__(self, "Unknown launcher: {}".format(name))

class MissingRequiredOption(Exception):
	def __init__(self, name):
		Exception.__init__(self, "Missing required option: {}".format(name))