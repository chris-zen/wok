from wok.task import task

@task.main()
def main():
	values, result = task.ports("x", "sum")

	count = 0
	nsum = 0
	for v in values:
		count += 1
		nsum += v

	task.logger.info("Sum of {0} numbers = {1}".format(count, nsum))
	
	result.send(nsum)

task.run()
