from wok.task import Task

task = Task()

log = task.logger()

@task.processor()
def square(x):

	square = x * x
	log.info("x = {0}, x^2 = {1}".format(x, square))
	
	return square

task.start()