import os
for k, v in os.environ.items():
	print "%s = %s" % (k, v)

from wok.task import Task

def run(task):

	# Initialization

	conf = task.conf
	
	log = task.logger()

	# Run
	
	if "in" not in task.ports:
		log.error("Port 'in' not defined")
		return -2

	if "out1" not in task.ports:
		log.error("Port 'out1' not defined")
		return -2
	if "out2" not in task.ports:
		log.error("Port 'out2' not defined")
		return -2

	s = 0.0
	k = 0
	for data in task.ports["in"]:
		log.info("Processing %s ..." % data)

		factor = float(data)
		l = int(200000 * factor)
		
		x = int(0)
		for i in xrange(l):
			x += i

		log.info("Result for %i iterations = %i" % (l, x))
		
		task.ports["out1"].write("%f\t%i" % (factor, x))

		s += factor
		k += 1

	mean = s / float(k)
	
	task.ports["out2"].write("%i\t%f\t%f" % (k, s, mean))
	
	log.info("%i data elements processed" % k)
	log.info("Elapsed time: %s" % task.elapsed_time())
	
	return 0
	
if __name__ == "__main__":
	Task(run).start()
