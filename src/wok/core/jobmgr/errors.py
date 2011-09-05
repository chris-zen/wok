# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

class UnknownScheduler(Exception):
	def __init__(self, name):
		Exception.__init__(self, "Unknown scheduler: {}".format(name))

class UnknownJob(Exception):
	def __init__(self, job_id):
		Exception.__init__(self, "Unknown job id: {}".format(job_id))