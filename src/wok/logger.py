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

import logging

_log_level_map = {
	"debug" : logging.DEBUG,
	"info" : logging.INFO,
	"warn" : logging.WARN,
	"error" : logging.ERROR,
	"critical" : logging.CRITICAL,
	"notset" : logging.NOTSET }

def initialize(conf):
	"""
	Initialize the logging system.

	* Configuration parameters:
	- log.format: Logger format
	"""
	
	if conf is not None and "format" in conf:
		format = conf["format"]
	else:
		format = "%(asctime)s %(name)s %(levelname) -5s : %(message)s"

	logging.basicConfig(format = format)
	
def get_logger(conf = None, name = None):
	"""
	Returns a logger.

	* Configuration parameters:

	- name: Logger name
	- level: Logging level: debug, info, warn, error, critical, notset
	"""

	if conf is None:
		conf = {}

	if name is None:
		name = ""
		if "name" in conf:
			name = conf["name"]

	log_level = "info"
	if "level" in conf:
		log_level = conf["level"].lower()
		if log_level not in _log_level_map:
			log_level = "notset"

	level = _log_level_map[log_level]

	log = logging.getLogger(name)
	log.setLevel(level)
	
	return log
