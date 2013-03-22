from wok.task import task

@task.generator()
def sequence(x_port):
	N = task.conf.get("N", 10, dtype=int)

	task.logger.info("N = {0}".format(N))

	for v in xrange(N):
		x_port.send(v)

task.run()
	
