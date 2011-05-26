from wok.task import Task

task = Task()

@task.generator()
def sequence(x):
	N = int(task.conf["N"])

	log = task.logger()
	log.info("N = {0}".format(N))

	for v in xrange(N):
		x.write(v)

task.start()
	