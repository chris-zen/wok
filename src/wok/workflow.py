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
        
    def run(self, jobs):
        self.scheduler.run(jobs)

### Workflow singleton

_workflow = None
        
def workflow():
    global _workflow
    
    if _workflow is None:
        _workflow = Workflow()

    return _workflow
