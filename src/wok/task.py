'''
Created on 08/07/2009

@author: chris
'''

from wok.job import Job

class Task:
    '''
    Represents a scheduled job.
    It has information about state of queued jobs.
    '''
    
    STATUS_ACTIVATION = 1
    STATUS_NOT_ACTIVATED = 2
    STATUS_DEP_WAITING = 3
    STATUS_EXECUTION = 4
    STATUS_PROC_WAITING = 5
    STATUS_TERMINATION = 6

    status_str = {
        STATUS_ACTIVATION : "Activation",
        STATUS_NOT_ACTIVATED : "Not activated",
        STATUS_DEP_WAITING : "Dependency waiting",
        STATUS_EXECUTION : "Execution",
        STATUS_PROC_WAITING : "Processor waiting",
        STATUS_TERMINATION : "Termination" }

    def __init__(self, job=Job(), status=STATUS_TERMINATION):
        self.job = job
        self.status = status
        
        # How many tasks is this task waiting for
        self.wait_counter = 0
        
        # Which tasks are waiting for this task
        self.waiting_tasks = []
        
        # jobs which this task is waiting for
        self.dependencies = []
        
        # jobs that should be invoked after execution
        self.invokations = []
    
    # This will be executed in the processor
    def execute(self):
        while self.status not in [Task.STATUS_DEP_WAITING, 
                                  Task.STATUS_TERMINATION,
                                  Task.STATUS_NOT_ACTIVATED]:
            
            if self.status == self.STATUS_ACTIVATION:
                if self.job.activate():
                    self.dependencies = self.job.dependencies()
                    if self.dependencies is None:
                        self.dependencies = []
                    if len(self.dependencies) > 0:
                        self.status = self.STATUS_DEP_WAITING
                    else:
                        self.status = self.STATUS_EXECUTION
                else:
                    self.status = self.STATUS_NOT_ACTIVATED
            elif self.status == self.STATUS_EXECUTION:
                self.invokations = self.job.execute()
                if self.invokations is None:
                    self.invokations = []
                self.status = self.STATUS_TERMINATION
    
    ### --------------------------------------
    
    def add_waiting_task(self, task):
        if task not in self.waiting_tasks:
            task.waits_on(self)
            self.waiting_tasks.append(task)
    
    def get_waiting_tasks(self):
        return self.waiting_tasks
    
    def waits_on(self, task):
        self.wait_counter += 1
    
    def notify_termination(self, task):
        self.wait_counter -= 1

    def is_waiting(self):
        return self.wait_counter > 0
    
    def __eq__(self, task):
        return self.job == task.job
    
    def __ne__(self, task):
        return self.job != task.job
    
    def __repr__(self):
        sb = [repr(self.job)]
        sb += [" (", self.status_str[self.status], ")"]
        if self.wait_counter > 0:
            sb += [" (", self.wait_counter, ")"]
        return "".join(sb)
