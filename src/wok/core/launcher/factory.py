# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.core.launcher.errors import UnknownLauncher
from wok.core.launcher.native import NativeLauncher
from wok.core.launcher.shell import ShellLauncher

__LAUNCHERS = {
	"native" : NativeLauncher,
	"shell" : ShellLauncher
}

def create_launcher(name, conf):
	if name not in __LAUNCHERS:
		raise UnknownLauncher(name)

	return __LAUNCHERS[name](conf)