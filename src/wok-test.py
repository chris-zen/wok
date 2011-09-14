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

instance_name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
install_path = os.path.dirname(os.path.realpath(__file__))

def add_options(parser):
	parser.add_option("-n", "--instance-name", dest="instance_name", default=instance_name, metavar="NAME",
			help="Set the instance name. Default name is built from the current date.")

initial_conf = {
	"wok" : {
		"execution" : {
			"mode" : {
				"native" : {
					"python" : {
						"lib_path" : [install_path]
					}
				}
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
	log.error("Missing the workflow definition file (.flow)")
	exit(-1)

wok_conf["__cwd"] = os.getcwd()

# expand variables

#conf.expand_vars()
#log.debug("Configuration: %s" % conf)

def main():
		wok = WokEngine(conf)
		wok.create_instance(conf.options.instance_name, conf.builder, conf.args[0])
		wok.start()

if __name__ == "__main__":
	main()
