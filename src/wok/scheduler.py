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
    
    # Ask Juanra how to merge schedule() and this function
    # checking whether the input is a single job or
    # a list of jobs
    def schedule_list(self, jobs):
        for job in jobs:
            self.schedule(job)
    
    def loop(self):
        pass

# Could it be an inner class of DefaultScheduler ???
class Task:
    '''
    Represents a scheduled job.
    It has information about state of queued jobs.
    '''
    
    STATUS_ACTIVATION = "Activation"
    STATUS_DEP_WAITING = "Dependency waiting"
    STATUS_EXECUTION = "Execution"
    STATUS_PROC_WAITING = "Processor waiting"
    STATUS_TERMINATION = "Termination"
     
    def __init__(self, job, status):
        self.job = job
        self.status = status
        
        # How many tasks is this task waiting for
        self.wait_counter = 0
        
        # Which tasks are waiting for this task
        self.waiting_tasks = []

    # TODO use mutex
    def add_waiting_task(self, task):
        if task not in self.waiting_tasks:
            task.inc_wait_counter()
            self.waiting_tasks.append(task)
    
    # TODO use mutex
    def get_waiting_tasks(self):
        return self.waiting_tasks
    
    # TODO use mutex
    def inc_wait_counter(self):
        self.wait_counter += 1
    
    # TODO use mutex
    def dec_wait_counter(self):
        self.wait_counter -= 1

    def __eq__(self, task):
        return self.job == task.job
    
    def __ne__(self, task):
        return self.job != task.job

class UnknownTaskStatus(Error):
    pass

class NoMoreTasks(Error):
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

    def schedule(self, job):
        task = self._find_task_by_job(job)
        if task is None:
            task = self._create_task(job)
            self._add_running_task(task)
    
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
                    self._dispatch_execution(task)
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
        self.waiting_tasks.put(task)
        
    def _remove_task(self, task):
        self.tasks.remove(task)
        
    def _next_task(self):
        if self._no_more_tasks():
            raise NoMoreTasks
        
        return self.running_tasks.get()

    def _no_more_tasks(self):
        return self.running_tasks.empty() and len(self.waiting_tasks) == 0
    
    def _notify_dep_waiting_tasks(self, task):
        raise NotImplemented("_notify_dep_waiting_tasks")
    
    def _dispatch_activation(self, task):
        job = task.job
        
        if job.activate():
            dep_jobs = job.dependencies()
            if len(dep_jobs) > 0:
                for job in dep_jobs:
                    dep_task = self._find_task_by_job(job)
                    if dep_task is None:
                        dep_task = self._create_task(dep_job)
                        self._add_running_task(dep_task)
                    
                    dep_task.add_waiting_task(task)
                
                task.status = Task.STATUS_DEP_WAITING
                self._add_waiting_task(task)
            else:
                task.status = Task.STATUS_EXECUTION
                self._add_running_task(task)
        else:
            self._remove_task(task)
            self._notify_dep_waiting_tasks(task)

    def _dispatch_execution(self, task):
        raise NotImplemented("_dispatch_execution")
    
    def _dispatch_termination(self, task):
        raise NotImplemented("_dispatch_termination")
