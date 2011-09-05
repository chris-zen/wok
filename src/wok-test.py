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
from wok.core.engine import WokEngine

# Wok initialization

def add_options(parser):
	pass

instance_name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
install_path = os.path.dirname(os.path.realpath(__file__))

initial_conf = {
	"wok" : {
		"__instance" : {
			"name" : instance_name
		},

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

if "wok" not in conf:
	print("Missing wok configuration")
	exit(-1)

wok_conf = conf["wok"]

# initialize logging

logger.initialize(wok_conf.get("log"))
log = logger.get_logger(wok_conf.get("log"), name = "wok-run")

# check arguments

if len(conf.args) != 1:
	log.error("Incorrect number of arguments")
	exit(-1)

wok_conf["__cwd"] = os.getcwd()

# expand variables

conf.expand_vars()
#log.debug("Configuration: %s" % conf)

def main():
		wok = WokEngine(conf)
		wok.create_instance(instance_name, conf.builder, conf.args[0])
		wok.start(async = True)
		wok.wait()
#		import time
#		time.sleep(1)
#		wok.stop()

if __name__ == "__main__":
	main()
