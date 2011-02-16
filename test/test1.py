import sys
import time

from intogen.analysis.task import Task

def run(task):

	# Initialization

	conf = task.conf
	
	log = task.logger()

	# Run
	
	if "in" not in task.ports:
		log.error("Port 'in' not defined")
		return -1

	for data in task.ports["in"]:
		log.info("Processing %s ..." % data)

		factor = float(data)
		
		x = long(0)
		for i in xrange(1000000000 * factor):
			x += i

		log.info("Result = %s" % str(x))
		
		task.ports["out"].write(str(x))

	log.info("Elapsed time: %s" % task.elapsed_time())
	
if __name__ == "__main__":
	Task(run).start()
