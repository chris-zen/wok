'''
Created on 28/06/2009

@author: chris
'''

from wok.scheduler import *
from wok.processor import *

class Workflow(object):
    '''
    Manager of workflows
    '''

    def __init__(self,
                 scheduler = DefaultScheduler(),
                 processor = DefaultProcessor()):
        self.scheduler = scheduler
        self.processor = processor
        
        self.scheduler.processor = processor
        
    def run(self, tasks, max_procs = 1):
        self.scheduler.max_procs = max_procs
        self.scheduler.run(tasks)
