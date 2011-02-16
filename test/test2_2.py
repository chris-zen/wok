
from wok.task import Task

def run(task):

	# Initialization

	conf = task.conf
	
	log = task.logger()

	# Run
	
	if "in" not in task.ports:
		log.error("Port 'in' not defined")
		return -2

	if "out" not in task.ports:
		log.error("Port 'out' not defined")
		return -2
		
	k = 0
	for data in task.ports["in"]:
		log.info("Processing %s ..." % data)

		fields = data.split("\t")
		
		factor = float(fields[0])
		l = int(200000 * factor)
		res = int(fields[1])
		
		x = int(0)
		for i in xrange(l):
			x += i
			
		if x == res:
			task.ports["out"].write("%f\t%s\tOk" % (factor, str(x)))
			log.info("Result for %i iterations matches %s" % (l, str(res)))
		else:
			task.ports["out"].write("%f\t%s\t%s\tWrong" % (factor, str(res), str(x)))
			log.info("Result for %i iterations DOESN'T match %s" % (l, str(res)))

		k += 1
	
	log.info("%i data elements processed" % k)
	log.info("Elapsed time: %s" % task.elapsed_time())
	
	return 0
	
if __name__ == "__main__":
	Task(run).start()
