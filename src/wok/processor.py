'''
Created on 29/06/2009

@author: chris
'''

from Queue import Queue

class Processor(object):
    '''
    Represents an execution processor 
    and defines the interface any processor should follow
    '''

    def execute(self, job):
        raise NotImplemented("abstract method")

class DefaultProcessor(Processor):
    '''
    Its an implementation of Processor for local execution among
    different number of cores/processors
    '''

    def __init__(self, max_procs = 1):
        self.max_procs = max_procs
        
        self.execute_queue = Queue()
    
    def execute(self, job):
        self.execute_queue.put(job)
        