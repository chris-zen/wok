# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

class WokAlreadyRunningError(Exception):
	pass

class WokInvalidOperationForStatusError(Exception):
	def __init__(self, op, status):
		Exception.__init__(self, "Invalid operation '{}' for current status '{}'".format(op, status))

class WokUninitializedError(Exception):
	pass