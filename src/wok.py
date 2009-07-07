'''
Created on 28/06/2009

@author: chris
'''

from wok import *
from wok.workflow import *
from wok.job import *

import logging

class Job1(Job):
    
    def execute(self):
        log = logging.getLogger(repr(self))
        log.info("Job1 executing...")

class Job2(Job):
    
    def dependencies(self):
        return [Job1("A1")]
    
    def execute(self):
        log = logging.getLogger(repr(self))
        log.info("Job2 executing...")
        
if __name__ == '__main__':

    j1 = Job1("A1")
    j2 = Job2("A2", p1 = "NA1", p2="NA2")
    
    logging.basicConfig()
    root_logger = logging.getLogger("")
    root_logger.setLevel(logging.DEBUG)
    root_logger.info("Running...")

    wf = Workflow(processor = None)
    wf.run(j2, j1)
    
    root_logger.info("Done.")