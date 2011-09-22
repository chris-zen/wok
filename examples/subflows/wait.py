from time import sleep
#from random import random

from wok.task import Task

task = Task()

@task.foreach()
def process(time):
	#delay = task.conf.get("delay", 1, dtype=int)
	#min_delay = task.conf.get("min_delay", delay, dtype=int)
	#max_delay = task.conf.get("max_delay", delay, dtype=int)
	#max_delay = max(min_delay, max_delay)
	#delay = min_delay + (max_delay - min_delay) * random()

	log = task.logger()
	log.info("Waiting for {:.2} seconds ...".format(time))
	sleep(time)

	return time

task.start()
	