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

import os.path
import glob

from wok.core.flow.reader import FlowReader

class FlowLoader(object):
	"""Represents a flow repository of flows.
	It implements a cache for the previously readed flows"""

	def __init__(self, flow_path = None):
		self.__flow_path = flow_path

		self.__flow_files = {}

		self.__flow_cache = {}

		self.__initialize()

	def __initialize(self):
		for path in self.__flow_path:
			if not os.path.exists(path):
				raise Exception("Path not found: {}".format(path))

			files = None
			if os.path.isdir(path):
				files = [flow_file for flow_file in glob.iglob(os.path.join(path, "*.flow"))]
			elif os.path.isfile(path):
				files = [path]

			if files is None:
				continue

			for flow_file in files:
				try:
					reader = FlowReader(flow_file)
					name, library, version = reader.read_meta()
					if name is None:
						continue

					uri = self.compose_uri(name, library, version)
					self.__flow_files[uri] = (flow_file, name, library, version)
				except:
					continue

	@property
	def flow_path(self):
		return self.__flow_path # TODO read-only

	@property
	def flow_files(self):
		return self.__flow_files # TODO read-only

	@property
	def flow_cache(self):
		return self.__flow_cache # TODO read-only

	def compose_uri(self, name, library = None, version = None):
		if library is not None:
			uri = "{}.{}".format(library, name)
		else:
			uri = name
		if version is not None:
			uri = "{}/{}".format(uri, version)
		return uri

	def load_from_file(self, path):
		reader = FlowReader(path)
		name, library, version = reader.read_meta()
		uri = self.compose_uri(name, library, version)
		#FIXME instance.py modifies model objects so we cannot cache them
		#if uri in self.__flow_cache:
		#	return self.__flow_cache[uri]

		flow = reader.read()
		self.__flow_cache[uri] = flow
		return flow

	def load_from_ref(self, ref):
		return self.load_from_uri(ref.uri)

	def load_from_canonical(self, canonical_name, version = None):
		if version is not None:
			uri = "{}/{}".format(canonical_name, version)
		return self.load_from_uri(uri)

	def load_from_uri(self, uri):
		if uri in self.__flow_cache:
			return self.__flow_cache[uri]

		if uri in self.__flow_files:
			reader = FlowReader(self.__flow_files[uri][0])
			flow = reader.read()
			self.__flow_cache[flow] = flow
			return flow

		raise Exception("Flow not found: {}".format(uri))
