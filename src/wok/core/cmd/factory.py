# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.core.cmd.errors import UnknownCmdBuilder
from wok.core.cmd.native import NativeCmdBuilder

__CMD_BUILDERS = {
	"native" : NativeCmdBuilder
}

def create_cmd_builder(name, conf):
	if name is None:
		name = "native"
	
	if name not in __CMD_BUILDERS:
		raise UnknownCmdBuilder(name)

	return __CMD_BUILDERS[name](conf)