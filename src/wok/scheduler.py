'''
Created on 29/06/2009

@author: chris
'''

from Queue import Queue
from wok.task import *

import threading

class Scheduler(object):
    '''
    The interface that any scheduler should follow
    '''

    def schedule(self, jobs):
        raise NotImplementedException("abstract method")
    
    def run(self, jobs):
        raise NotImplementedException("abstract method")

class UnknownTaskStatus(Exception):
    pass

class NoMoreTasks(Exception):
    pass

class DefaultSchedulerWorker(threading.Thread):
    '''
    DefaultScheduler working thread that dispatchs task execution
    '''
    
    def __init__(self, scheduler, name=None):
        threading.Thread.__init__(self, name=name)
        
        self.scheduler = scheduler
        
    def run(self):
        while True:
            task = self.scheduler.get_task()
            if task == self.scheduler.LAST_TASK:
                break
            
            task.execute()
            
            self.scheduler.put_task(task)

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
    
    # Used to stop working threads
    LAST_TASK = Task()
    
    def __init__(self, num_procs = 2):
        self._running_tasks = []
        
        self._waiting_tasks = []
        
        self._tasks = []
        
        self._tasks_cond = threading.Condition()
        
        self._workers = []
        
        for i in range(num_procs):
            worker = DefaultSchedulerWorker(scheduler = self, name="sched_worker_" + str(i))
            self._workers.append(worker)

    def schedule(self, jobs):
        self._tasks_cond.acquire()
        self._invoke(jobs)
        self._tasks_cond.release()
        
    def run(self, jobs = []):
        self.schedule(jobs)
        
        for worker in self._workers:
            worker.start()
            
        for worker in self._workers:
            worker.join()
            
    def stop(self):
        self._tasks_cond.acquire()
        self._invoke([self.LAST_TASK])
        self._tasks_cond.release()
    
    def get_task(self):
        self._tasks_cond.acquire()
        task = None
        while task is None:
            if self._no_tasks():
                task = self.LAST_TASK
            else:
                if len(self._running_tasks) == 0:
                    self._tasks_cond.wait()
    
                if len(self._running_tasks) != 0:
                    task = self._running_tasks.pop(0)

        self._tasks_cond.release()
        return task
    
    def put_task(self, task):
        self._tasks_cond.acquire()
        if task.status == Task.STATUS_ACTIVATION:
            self._add_running_task(task)
        elif task.status == Task.STATUS_DEP_WAITING:
            self._invoke(task.dependencies, task)
            self._add_waiting_task(task)
        elif task.status == Task.STATUS_EXECUTION:
            self._add_running_task(task)
        elif task.status == Task.STATUS_TERMINATION:
            self._notify_termination(task)
            self._invoke(task.invokations)
            self._remove_task(task)
        elif task.status == Task.STATUS_NOT_ACTIVATED:
            self._notify_termination(task)
            self._remove_task(task)
        else:
            raise NotImplemented("put_task: " + Task.status_str[task.status])
        self._tasks_cond.release()
    
    ### Running tasks management
    
    def _add_running_task(self, task):
        self._running_tasks.append(task)
        self._tasks_cond.notify()
    
    def _get_running_task(self):
        if len(self._running_tasks) == 0:
            self._tasks_cond.wait()

        return self._running_tasks.pop(0)
    
    ### Waiting tasks management
    
    def _add_waiting_task(self, task):
        self._waiting_tasks.append(task)
        
    def _remove_waiting_task(self, task):
        self._waiting_tasks.remove(task)
        
    ### Tasks management (callers are responsible for locking)
    
    def _find_task_by_job(self, job):
        for task in self._tasks:
            if task.job == job:
                return task
            
        return None
    
    def _create_task(self, job, status = Task.STATUS_ACTIVATION):
        task = Task(job, status)
        self._tasks.append(task)
        self._tasks_cond.notify()
        return task
    
    def _remove_task(self, task):
        self._tasks.remove(task)
        self._tasks_cond.notify()
    
    def _invoke(self, jobs, wtask = None):
        for job in jobs:
            task = self._find_task_by_job(job)
            if task is None:
                task = self._create_task(job)
                self._add_running_task(task)
            
            if wtask is not None:
                task.add_waiting_task(wtask)
    
    def _notify_termination(self, task):
        wtasks = task.get_waiting_tasks()
        for wtask in wtasks:
            wtask.notify_termination(task)
            if not wtask.is_waiting():
                self._remove_waiting_task(wtask)
                if wtask.status == Task.STATUS_DEP_WAITING:
                    wtask.status = Task.STATUS_EXECUTION
                    self._add_running_task(wtask)
                else:
                    raise NotImplemented("_notify_termination: " + Task.status_str[wtask.status])

    def _no_tasks(self):
        return len(self._tasks) == 0 \
                and len(self._running_tasks) == 0 \
                and len(self._waiting_tasks) == 0
    
    ### Deprecated
        
    def _next_task(self):
        if self._no_more_tasks():
            raise NoMoreTasks
        
        return self._running_tasks.get()

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
