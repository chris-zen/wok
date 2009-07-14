'''
Created on 28/06/2009

@author: chris
'''

from wok.scheduler import *

class Workflow(object):
    '''
    Manager of workflows
    '''

    def __init__(self, scheduler = DefaultScheduler()):
        self.scheduler = scheduler
                
    def run(self, tasks):
        self.scheduler.run(tasks)
