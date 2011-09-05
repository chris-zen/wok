# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.core.portio.filedata import TYPE_FILE_DATA, FileData
from wok.core.portio.pathdata import TYPE_PATH_DATA, PathData
from wok.core.portio.multidata import TYPE_MULTI_DATA, MultiData

_PORT_DATA_TYPES = {
	TYPE_FILE_DATA : FileData,
	TYPE_PATH_DATA : PathData,
	TYPE_MULTI_DATA : MultiData
}

class PortDataFactory(object):
	@staticmethod
	def create_port_data(conf):
		if "type" not in conf:
			raise Exception("Cannot create the port data without knowing the type")
		
		return _PORT_DATA_TYPES[conf["type"]](conf = conf)

