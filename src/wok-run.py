#!/usr/bin/env python

import os
import uuid

from wok import logger
from wok.config import Config
from wok.reader import FlowReader
from wok.engine import WokEngine

# Wok initialization

def add_options(parser):
	pass

initial_conf = {
	"wok" : {
		"__instance" : {
			"name" : str(uuid.uuid4())
		}
	}
}

conf = Config(
	initial_conf = initial_conf,
	args_usage = "<flow-file>",
	add_options = add_options)

if "wok" not in conf:
	print("Missing wok configuration")
	exit(-1)

wok_conf = conf["wok"]

logger.initialize(wok_conf.get("log"))
log = logger.get_logger(wok_conf.get("log"))

if len(conf.args) != 1:
	log.error("Incorrect number of arguments")
	exit(-1)

flow_arg = conf.args[0]
flow_path = os.path.dirname(os.path.abspath(flow_arg))
wok_conf["__flow.path"] = flow_path
wok_conf["__flow.file"] = os.path.basename(flow_arg)

wok_conf["__cwd"] = os.getcwd()

conf.expand_vars()

#log.debug("Configuration: %s" % conf)

reader = FlowReader(flow_arg)
flow = reader.read()
reader.close()

wok = WokEngine(conf, flow)

def main():
	server_mode = wok_conf.get("server.enabled", False, dtype=bool)
	if server_mode:
		from wok.server import app
		app.config["WOK"] = wok
		server_host = wok_conf.get("server.host", "localhost", dtype=str)
		server_port = wok_conf.get("server.port", 5000, dtype=int)
		server_debug = wok_conf.get("server.debug", False, dtype=bool)

		app.run(host=server_host, port=server_port, debug = server_debug)
	else:
		wok.start(async = False)

if __name__ == "__main__":
	main()
