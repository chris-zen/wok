# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.core.jobmgr.errors import *
from wok.core.jobmgr.dummy import DummyJobManager
#from wok.core.jobmgr.drmaa import DrmaaJobManager
from wok.core.jobmgr.mcore import McoreJobManager

JOB_MANAGERS = {
	"dummy" : DummyJobManager,
#	"drmaa" : DrmaaJobManager,
	"mcore" : McoreJobManager
}

def create_job_manager(name, engine, conf):
	if name is None or name == "default":
		name = "mcore"

	if name not in JOB_MANAGERS:
		raise UnknownScheduler(name)

	return JOB_MANAGERS[name](engine, conf)
