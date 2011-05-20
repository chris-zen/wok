# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

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
