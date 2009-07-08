'''
Created on 08/07/2009

@author: chris
'''

from wok import *
from wok.workflow import *
from wok.job import *

import logging

done = []

class JobA(Job):
    
    def activate(self):
        return repr(self) not in done
    
    def execute(self):
        log = logging.getLogger(repr(self))
        log.info(repr(self) + " executing...")
        import time, random
        time.sleep(random.randint(2, 3))
        done.append(repr(self))

class JobB(Job):
    
    def activate(self):
        return repr(self) not in done
    
    def dependencies(self):
        return [JobA("A" + str(i)) for i in range(5, 7)]
    
    def execute(self):
        log = logging.getLogger(repr(self))
        log.info(repr(self) + " executing...")
        import time
        time.sleep(4)
        done.append(repr(self))
        return [JobC("C" + str(i)) for i in range(3)]

class JobC(Job):
    def execute(self):
        log = logging.getLogger(repr(self))
        log.info(repr(self) + " executing...")
        import time, random
        time.sleep(random.randint(2, 4))
        
if __name__ == '__main__':

    a = [JobA("A" + str(i)) for i in range(3)]
    a.append(JobB("B", p1 = "P1", p2="P2"))
    #j1 = Job1("A1")
    #j2 = Job2("A2", p1 = "NA1", p2="NA2")
    
    logging.basicConfig()
    root_logger = logging.getLogger("")
    root_logger.setLevel(logging.DEBUG)
    root_logger.info("Running...")

    wf = Workflow(processor = None)
    wf.run(a)
    
    root_logger.info("Done.")
