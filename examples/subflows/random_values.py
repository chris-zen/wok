from wok.task import Task

task = Task()

@task.generator()
def sequence(value):
	N = int(task.conf["N"])
	MIN = float(task.conf["MIN"])
	MAX = float(task.conf["MAX"])

	log = task.logger()
	log.info("N = {}, MIN = {}, MAX = {}".format(N, MIN, MAX))

	for _ in xrange(N):
		value.write((random() * (MAX - MIN)) + MIN)

task.start()
	