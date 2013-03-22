from wok.task import task

@task.generator()
def sequence(value):
	conf = task.conf
	start = conf.get("start", 0, dtype=int)
	size = conf.get("size", 100, dtype=int)

	task.logger.info("Generating values from {0} to {1}".format(start, start + size - 1))

	for v in xrange(start, start + size):
		value.send(v)

task.run()
