#!/usr/bin/env python

import os

from wok import logger
from wok.config import Config
from wok.reader import FlowReader
from wok.engine import WokEngine

def add_options(parser):
	pass

def main():
	from optparse import OptionParser

	conf = Config(args_usage = "<flow-file>", add_options = add_options)
	
	if "wok" not in conf:
		print("Missing wok configuration")
		exit(-1)
		
	wok_conf = conf["wok"]
	
	logger.initialize(wok_conf)
	log = logger.get_logger(wok_conf)
	
	if len(conf.args) != 1:
		log.error("Incorrect number of arguments")
		exit(-1)
	
	flow_arg = conf.args[0]
	flow_path = os.path.dirname(os.path.abspath(flow_arg))
	wok_conf["flow_path"] = flow_path
	wok_conf["flow_file"] = os.path.basename(flow_arg)

	wok_conf["cwd"] = os.getcwd()

	conf.expand_vars()
	
	log.debug("Configuration: %s" % conf)
	
	reader = FlowReader(flow_arg)
	flow = reader.read()
	reader.close()
	
	wok = WokEngine(conf)
	wok.run(flow)
	wok.exit()
	
if __name__ == "__main__":
	main()
