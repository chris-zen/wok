from wok.task import Task

task = Task()

@task.generator()
def sequence(x_port):
	N = task.conf.get("N", 10, dtype = int)

	log = task.logger()
	log.info("N = {0}".format(N))

	for v in xrange(N):
		x_port.send(v)

task.start()
	
