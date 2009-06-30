'''
Created on 29/06/2009

@author: chris
'''

class Scheduler(object):
    '''
    The interface that any scheduler should follow
    '''

    def schedule(self):
        pass
    
    def loop(self):
        pass


class Task:
    '''
    Represents a scheduled job.
    It has information about state of queued jobs.
    '''
    
    def __init__(self, job):
        self.job = job


class DefaultScheduler(Scheduler):
    '''
    Default implementation of the scheduler interface.
    
    It has 3 queues for jobs in different states:
    - activation: for jobs that requires checking for activation
    - execution: for jobs waiting for the processor to run it
    - termination: for jobs that have finished execution
    
    It has 2 list for jobs that need to be tracked:
    - dependencies: for jobs waiting for dependencies to be executed
    - processor: for jobs that are being executed by the processor    
    '''
    
    def __init__(self):
        self.activation_q = Queue()
        self.execution_q = Queue()
        self.termination_q = Queue()

        self.dependencies_w = []
        self.processor_w = []

    def schedule(self, job):
        self.activation_q.put(Task(job))

    # Ask Juanra how to merge schedule() and this function
    # checking whether the input is a single job or
    # a list of jobs
    def schedule_list(self, jobs):
        for job in jobs:
            self.activation_q.put(Task(job))
        
    def loop(self):
        '''
        Loops dispatching events until all the jobs has been terminated.
        '''
        
        while True:
            if not self.termination_q.empty():
                dispatch_termination(self.termination_q.get())
                continue
            
            if not self.execution_q.empty():
                dispatch_execution(self.execution_q.get())
                continue
        
            if not self.execution_q.empty():
                dispatch_execution(self.execution_q.get())
                continue
            
            if not self.activation_q.empty():
                dispatch_activation(self.activation_q.get())
                continue
            
            if (self.activation_q.empty() and 
                self.dependencies_q.empty() and
                self.execution_q.empty() and
                self.processor_q.empty() and
                self.termination_q.empty()):
                break

    def dispatch_activation(self, task):
        pass
    
    def dispatch_execution(self, task):
        pass
    
    def dispatch_termination(self, task):
        pass
    