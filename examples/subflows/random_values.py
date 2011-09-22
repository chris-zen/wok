from random import random

from wok.task import Task

task = Task()

@task.generator()
def sequence(value_port):
	# get the configuration
	conf = task.conf

	# get parameters

	# get N as an integer, it defaults to 100
	N = conf.get("N", 100, dtype = int)

	# get the MIN, it defaults to 1
	MIN = conf.get("MIN", 1.0, dtype = float)

	# get the MAX, it defaults to 1
	MAX = conf.get("MAX", 4.0, dtype = float)

	# get logger
	log = task.logger()
	log.info("N = {}, MIN = {}, MAX = {}".format(N, MIN, MAX))

	# generate values and send them through the value_port
	for _ in xrange(N):
		value_port.send((random() * (MAX - MIN)) + MIN)

task.start()
	