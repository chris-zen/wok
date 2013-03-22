from wok.task import task

@task.main()
def main():

	values, count_port, sum_port = task.ports("x", "count", "sum")

	count = 0
	sum = 0
	for v in values:
		task.logger.info("value = {0}".format(v))
		count += 1
		sum += v

	task.logger.info("Sum of {0} numbers = {1}".format(count, sum))

	count_port.send(count)
	sum_port.send(sum)

task.run()
