# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.scheduler.drmaa_sched import DrmaaJobScheduler
from wok.scheduler.mcore import McoreJobScheduler

JOB_SCHEDULERS = {
	"drmaa" : DrmaaJobScheduler,
	"mcore" : McoreJobScheduler
}

def create_job_scheduler(name, conf):
	if name == "default":
		name = "mcore"

	if name not in JOB_SCHEDULERS:
		raise Exception("Unknown scheduler: %s" % name)

	return JOB_SCHEDULERS[name](conf)
