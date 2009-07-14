'''
Created on 08/07/2009

@author: chris
'''

from wok import *
from wok.task import Task
from wok.workflow import *

import logging

done = []

class TaskA(Task):
    
    def activate(self):
        return repr(self) not in done
    
    def execute(self):
        log = logging.getLogger(repr(self))
        log.info(repr(self) + " executing...")
        import time, random
        time.sleep(random.randint(1, 2))
        done.append(repr(self))

class TaskB(Task):
    
    def activate(self):
        return repr(self) not in done
    
    def dependencies(self):
        return [TaskA("A" + str(i)) for i in range(5, 7)]
    
    def execute(self):
        log = logging.getLogger(repr(self))
        log.info(repr(self) + " executing...")
        import time
        time.sleep(1)
        done.append(repr(self))
        
    def invoke(self):
        return [TaskC("C" + str(i)) for i in range(3)]

class TaskC(Task):
    def execute(self):
        log = logging.getLogger(repr(self))
        log.info(repr(self) + " executing...")
        import time, random
        time.sleep(random.randint(1, 2))

if __name__ == '__main____':

    a = [TaskA("A" + str(i)) for i in range(3)]
    a.append(TaskB("B", p1 = "P1", p2="P2"))
    #j1 = Task1("A1")
    #j2 = Task2("A2", p1 = "NA1", p2="NA2")
    
    logging.basicConfig()
    root_logger = logging.getLogger("")
    root_logger.setLevel(logging.DEBUG)
    root_logger.info("Running...")

    wf = Workflow()
    wf.run(a)
    
    root_logger.info("Done.")
