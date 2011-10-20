###############################################################################
#
#    Copyright 2009-2011, Universitat Pompeu Fabra
#
#    This file is part of Wok.
#
#    Wok is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Wok is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses
#
###############################################################################

from wok.scheduler.mcore import McoreJobScheduler

JOB_SCHEDULERS = {
	"mcore" : McoreJobScheduler
}

try:
	from wok.scheduler.drmaa_ import DrmaaJobScheduler
	JOB_SCHEDULERS["drmaa"] = DrmaaJobScheduler
except:
	from wok.logger import get_logger
	log = get_logger()
	log.warn("DRMAA is not installed in this machine")


def create_job_scheduler(name, conf):
	if name == "default":
		name = "mcore"

	if name not in JOB_SCHEDULERS:
		raise Exception("Unknown scheduler: %s" % name)

	return JOB_SCHEDULERS[name](conf)
