from wok.task import Task

task = Task()

nsum = 0

@task.main()
def main():
	log = task.logger()

	values, result = task.ports("x", "sum")

	count = 0
	nsum = 0
	for v in values:
		count += 1
		nsum += v

	log.info("Sum of {0} numbers = {1}".format(count, nsum))
	
	result.send(nsum)

task.start()
