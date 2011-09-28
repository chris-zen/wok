from wok.task import Task

task = Task()

sum = 0

@task.main()
def main():
	log = task.logger()

	values, count_port, sum_port = task.ports("x", "count", "sum")

	count = 0
	sum = 0
	for v in values:
		log.info("value = {0}".format(v))
		count += 1
		sum += v

	log.info("Sum of {0} numbers = {1}".format(count, sum))

	count_port.send(count)
	sum_port.send(sum)

task.start()
