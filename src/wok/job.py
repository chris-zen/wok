'''
Created on 30/06/2009

@author: chris
'''

from wok.task import Task

class Job:
    '''
    Represents a scheduled task.
    It has information about state of queued tasks.
    '''
    
    STATUS_ACTIVATION = 1
    STATUS_NOT_ACTIVATED = 2
    STATUS_DEP_WAITING = 3
    STATUS_EXECUTION = 4
    STATUS_PROC_WAITING = 5
    STATUS_INVOCATION = 6
    STATUS_TERMINATION = 7

    status_str = {
        STATUS_ACTIVATION : "Activation",
        STATUS_NOT_ACTIVATED : "Not activated",
        STATUS_DEP_WAITING : "Dependency waiting",
        STATUS_EXECUTION : "Execution",
        STATUS_PROC_WAITING : "Processor waiting",
        STATUS_INVOCATION : "Invocation",
        STATUS_TERMINATION : "Termination" }

    def __init__(self, task=Task(), status=STATUS_TERMINATION):
        self.task = task
        self.status = status
        
        # How many tasks is this task waiting for
        self.wait_counter = 0
        
        # Which jobs are waiting for this job
        self.waiting_jobs = []
        
        # tasks this job will wait for
        self.dependencies = []
        
        # tasks that should be invoked after execution
        self.invocations = []
    
    # This will be executed in the processor
    def execute(self):
        while self.status not in [Job.STATUS_DEP_WAITING, 
                                  Job.STATUS_TERMINATION]:
            
            if self.status == Job.STATUS_ACTIVATION:
                if self.task.activate():
                    self.dependencies = self.task.dependencies()
                    if self.dependencies is None:
                        self.dependencies = []
                    if len(self.dependencies) > 0:
                        self.status = Job.STATUS_DEP_WAITING
                    else:
                        self.status = Job.STATUS_EXECUTION
                else:
                    self.status = Job.STATUS_INVOCATION
            elif self.status == Job.STATUS_EXECUTION:
                self.task.execute()
                self.status = Job.STATUS_INVOCATION
            elif self.status == Job.STATUS_INVOCATION:
                self.invocations = self.task.invoke()
                if self.invocations is None:
                    self.invocations = []
                self.status = Job.STATUS_TERMINATION
    
    ### --------------------------------------
    
    def add_waiting_job(self, job):
        if job not in self.waiting_jobs:
            job.waits_on(self)
            self.waiting_jobs.append(job)
    
    def get_waiting_jobs(self):
        return self.waiting_jobs
    
    def waits_on(self, job):
        self.wait_counter += 1
    
    def notify_termination(self, job):
        self.wait_counter -= 1

    def is_waiting(self):
        return self.wait_counter > 0
    
    def __eq__(self, job):
        return self.task == job.task
    
    def __ne__(self, task):
        return self.task != job.task
    
    def __repr__(self):
        sb = [repr(self.task)]
        sb += [" (", Job.status_str[self.status], ")"]
        if self.wait_counter > 0:
            sb += [" (", self.wait_counter, ")"]
        return "".join(sb)
