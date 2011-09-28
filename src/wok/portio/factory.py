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

from filedata import TYPE_FILE_DATA, FileData
from pathdata import TYPE_PATH_DATA, PathData
from multidata import TYPE_MULTI_DATA, MultiData

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

