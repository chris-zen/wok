'''
Created on 29/06/2009

@author: chris
'''

from Queue import Queue

class Scheduler(object):
    '''
    The interface that any scheduler should follow
    '''

    def schedule(self, jobs):
        raise NotImplementedException("abstract method")
    
    def loop(self):
        raise NotImplementedException("abstract method")

# Could it be an inner class of DefaultScheduler ???
class Task:
    '''
    Represents a scheduled job.
    It has information about state of queued jobs.
    '''
    
    STATUS_ACTIVATION = 1
    STATUS_DEP_WAITING = 2
    STATUS_EXECUTION = 3
    STATUS_PROC_WAITING = 4
    STATUS_TERMINATION = 5

    status_str = {
        STATUS_ACTIVATION : "Activation",
        STATUS_DEP_WAITING : "Dependency waiting",
        STATUS_EXECUTION : "Execution",
        STATUS_PROC_WAITING : "Processor waiting",
        STATUS_TERMINATION : "Termination" }
    
    def __init__(self, job, status):
        self.job = job
        self.status = status
        
        # How many tasks is this task waiting for
        self.wait_counter = 0
        
        # Which tasks are waiting for this task
        self.waiting_tasks = []
    
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

class UnknownTaskStatus(Exception):
    pass

class NoMoreTasks(Exception):
    pass

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
        self.running_tasks = Queue()
        self.waiting_tasks = []
        
        self.tasks = []

    def schedule(self, jobs):
        self._invoke(jobs)
        
    def loop(self):
        '''
        Loops dispatching events until all the jobs has been terminated.
        '''
        
        try:
            while True:
                task = self._next_task()
                if task.status == Task.STATUS_ACTIVATION:
                    self._dispatch_activation(task)
                elif task.status == Task.STATUS_EXECUTION:
                    self._dispatch_execution(task)
                elif task.status == Task.STATUS_TERMINATION:
                    self._dispatch_termination(task)
                else:
                    raise UnknownTaskStatus(task.status)
        
        except NoMoreTasks:
            return
    
    def _find_task_by_job(self, job):
        for task in self.tasks:
            if task.job == job:
                return task
            
        return None
    
    def _create_task(self, job, status = Task.STATUS_ACTIVATION):
        task = Task(job, status)
        self.tasks.append(task)
        return task

    def _add_running_task(self, task):
        self.running_tasks.put(task)
    
    def _add_waiting_task(self, task):
        self.waiting_tasks.append(task)
        
    def _remove_waiting_task(self, task):
        self.waiting_tasks.remove(task)
    
    def _remove_task(self, task):
        self.tasks.remove(task)
        
    def _next_task(self):
        if self._no_more_tasks():
            raise NoMoreTasks
        
        return self.running_tasks.get()

    def _no_more_tasks(self):
        return self.running_tasks.empty() and len(self.waiting_tasks) == 0
    
    def _notify_termination(self, task):
        wtasks = task.get_waiting_tasks()
        for wtask in wtasks:
            wtask.notify_termination(task)
            if not wtask.is_waiting():
                self._remove_waiting_task(wtask)
                wtask.status = Task.STATUS_EXECUTION
                self._add_running_task(wtask)
    
    def _invoke(self, jobs, wtask = None):
        for job in jobs:
            task = self._find_task_by_job(job)
            if task is None:
                task = self._create_task(job)
                self._add_running_task(task)
            
            if wtask is not None:
                task.add_waiting_task(wtask)
            
    def _dispatch_activation(self, task):
        job = task.job
        
        if job.activate():
            dep_jobs = job.dependencies()
            if len(dep_jobs) > 0:
                self._invoke(dep_jobs, task)
                task.status = Task.STATUS_DEP_WAITING
                self._add_waiting_task(task)
            else:
                task.status = Task.STATUS_EXECUTION
                self._add_running_task(task)
        else:
            self._remove_task(task)
            self._notify_dep_waiting_tasks(task)

    def _dispatch_execution(self, task):
        if self.processor is None:
            task.status = Task.STATUS_PROC_WAITING
            task.job.execute()
            task.status = Task.STATUS_TERMINATION
            self._add_running_task(task)
        else:
            task.status = Task.STATUS_PROC_WAITING
            self._add_waiting_task(task)
            self.processor.execute(task.job)
    
    def _dispatch_termination(self, task):
        ivk_jobs = task.job.invokes()
        self._invoke(ivk_jobs)
        self._remove_task(task)
        self._notify_termination(task)
