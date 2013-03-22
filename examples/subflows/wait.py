from time import sleep

from wok.task import task

@task.foreach()
def process(time):
	#delay = task.conf.get("delay", 1, dtype=int)
	#min_delay = task.conf.get("min_delay", delay, dtype=int)
	#max_delay = task.conf.get("max_delay", delay, dtype=int)
	#max_delay = max(min_delay, max_delay)
	#delay = min_delay + (max_delay - min_delay) * random()

	task.logger.info("{}: {}".format(type(time), repr(time)))
	#if time > 1.5:
	#	return -1
	task.logger.info("Waiting for {:.2} seconds ...".format(time))
	sleep(time)

	return time

task.run()
	
