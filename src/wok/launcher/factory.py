# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.launcher.python import PythonLauncher
from wok.launcher.shell import ShellLauncher

LAUNCHERS = {
	"shell" : ShellLauncher,
	"python" : PythonLauncher
}

def create_launcher(name, conf):
	if name is None:
		name = "shell"

	if name not in LAUNCHERS:
		raise Exception("Unknown launcher")

	return LAUNCHERS[name](conf)
