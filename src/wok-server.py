#!/usr/bin/env python

# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

import os
import os.path
from datetime import datetime

from wok import logger
from wok.config import OptionsConfig
from wok.element import DataElement
from wok.engine import WokEngine

# Wok initialization

def add_options(parser):
	pass

instance_name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
install_path = os.path.dirname(os.path.realpath(__file__))

initial_conf = {
	"wok" : {
		"launchers" : {
			"python" : {
				"pythonpath" : [install_path]
			}
		}
	}
}

conf = OptionsConfig(
	initial_conf = initial_conf,
	args_usage = "<flow-file>",
	add_options = add_options)

wok_conf = conf["wok"]

# initialize logging

logger.initialize(wok_conf.get("log"))
log = logger.get_logger(wok_conf.get("log"), name = "wok-server")

# read the workflow definition

wok_conf["__cwd"] = os.getcwd()

# expand variables

conf.expand_vars()
#log.debug("Configuration: %s" % conf)

def main():
	from wok.server import app
	wok = WokEngine(conf)
	app.config["WOK"] = wok
	server_host = wok_conf.get("server.host", "localhost", dtype=str)
	server_port = wok_conf.get("server.port", 5000, dtype=int)
	server_debug = wok_conf.get("server.debug", False, dtype=bool)

	log.info("Running server at http://{0}:{1}".format(server_host, server_port))

	log_conf = wok_conf.get("server.log")
	if log_conf is None:
		log_conf = DataElement()
		log_conf["level"] = "warn"
	app_log = logger.get_logger(conf = log_conf, name = "werkzeug")
	app_log.info("Log configured")

	app.run(host = server_host, port = server_port, debug = server_debug)

if __name__ == "__main__":
	main()
