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

import psutil
import sys
import os
import shlex
import multiprocessing as mp
from time import sleep
from datetime import datetime

__K = 1024
__M = __K * 1024
__G = __M * 1024
__T = __G * 1024

def __hmem(m):
	if m < __K:
		return "%sb B" % m
	elif m < __M:
		return "%.1f K" % float(m / __K)
	elif m < __G:
		return "%.1f M" % float(m / __M)
	elif m < __T:
		return "%.1f G" % float(m / __G)
	else:
		return "%s B" % m

def __monproc(pid, stats, interval):
	max_vms = 0
	max_rss = 0
	f = None
	try:
		start = datetime.now()
		psp = psutil.Process(pid)
		f = open(stats, "w")
		f.write("TIMESTAMP ELAPSED MEM_VMS MEM_RSS\n")
		while psutil.pid_exists(pid):
			now = datetime.now()
			timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
			elapsed = str((now - start).total_seconds())
			mem = psp.get_memory_info()
			max_vms = max(max_vms, mem.vms)
			max_rss = max(max_rss, mem.rss)
			f.write("%s %s %s %s\n" % (timestamp, elapsed, mem.vms, mem.rss))
			f.flush()
			sleep(interval)
	except:
		pass
	finally:
		if f is not None:
			f.close()

	return (max_vms, max_rss)

def __logproc(pid, r, w, append_timestamp):
	try:
		psp = psutil.Process(pid)
		for line in iter(r.readline, ""):
			if not psutil.pid_exists(pid):
				break

			if append_timestamp:
				timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				w.write(timestamp)
				w.write(" ")

			mem = psp.get_memory_info()

			w.write("%s %s %s\n" % (__hmem(mem.vms), __hmem(mem.rss), line.rstrip()))
	except:
		pass

def __run_child(cmd, env, stdout, stderr):
	args = shlex.split(cmd)

	os.dup2(stdout.fileno(), sys.stdout.fileno())
	os.dup2(stderr.fileno(), sys.stderr.fileno())

	if env is None:
		os.execvp(args[0], args)
	else:
		os.execvpe(args[0], args, env)

def call(cmd, env = None, shell = False, stats = None, interval = 10, logout = False, logerr = False, logtimestamp = False, name = ""):

	if logout:
		r, w = os.pipe()
		outr = os.fdopen(r, "r")
		outw = os.fdopen(w, "w")
	else:
		outw = sys.stdout

	if logerr:
		r, w = os.pipe()
		errr = os.fdopen(r, "r")
		errw = os.fdopen(w, "w")
	else:
		errw = sys.stderr

	pid = os.fork()
	if pid == 0:
		__run_child(cmd, env, outw, errw)

	if stats is not None:
		pool = mp.Pool(1)
		max_mem = pool.apply_async(__monproc, (pid, stats, interval, ))

	if logout:
		outp = mp.Process(name = "%s-logout" % name, target = __logproc, args = (pid, outr, sys.stdout, logtimestamp))
		outp.start()

	if logerr:
		errp = mp.Process(name = "%s-logerr" % name, target = __logproc, args = (pid, errr, sys.stderr, logtimestamp))
		errp.start()

	exit_code = os.waitpid(pid, 0)[1] >> 8

	stats_results = {}

	if stats is not None:
		mem = max_mem.get()
		stats_results["max_vms"] = mem[0]
		stats_results["max_rss"] = mem[1]
		stats_results["max_vms_h"] = __hmem(mem[0])
		stats_results["max_rss_h"] = __hmem(mem[1])

	if logout:
		outp.terminate()
		outp.join()

	if logerr:
		errp.terminate()
		errp.join()

	return (exit_code, stats_results)
