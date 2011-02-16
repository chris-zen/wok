import os

from wok.task import Task

def run(task):

	# Initialization

	conf = task.conf
	
	log = task.logger()

	# Run
	
	if "in" not in task.ports:
		log.error("Port 'in' not defined")
		return -2
		
	if "TEST_MSG" in os.environ:
		log.info(os.environ["TEST_MSG"])
	else:
		log.info("Hello, no msg defined")

	if "TEST1" in os.environ:
		log.info(os.environ["TEST1"])

	in_port = task.ports["in"]
	
	log.info("Number of port elements = %i" % in_port.size())

	data = task.ports["in"].read()
	while data is not None:
		log.info("Data = %s ..." % data)
		data = task.ports["in"].read()
		
	log.info("Elapsed time: %s" % task.elapsed_time())
	
	return 0
	
if __name__ == "__main__":
	Task(run).start()
