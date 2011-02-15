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
	if "log.format" in conf:
		format = conf["log.format"]
	else:
		format = "%(asctime)s %(name)s %(levelname) -5s : %(message)s"

	logging.basicConfig(format = format)
	
def get_logger(conf, name = None):
	"""
	Returns a logger.

	* Configuration parameters:

	- log.name: Logger name
	- log.level: Logging level: debug, info, warn, error, critical, notset
	"""

	if name is None:
		name = ""
		if "log.name" in conf:
			name = conf["log.name"]

	log_level = "info"
	if "log.level" in conf:
		log_level = conf["log.level"].lower()
		if log_level not in _log_level_map:
			log_level = "notset"

	level = _log_level_map[log_level]

	log = logging.getLogger(name)
	log.setLevel(level)
	
	return log
