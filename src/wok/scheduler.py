'''
Created on 29/06/2009

@author: chris
'''

import threading

from Queue import Queue

from wok.job import Job

class Scheduler(object):
    '''
    The interface that any scheduler should follow
    '''

    def schedule(self, tasks):
        raise NotImplementedException("abstract method")
    
    def run(self, tasks):
        raise NotImplementedException("abstract method")

class UnknownJobStatus(Exception):
    pass

class DefaultSchedulerWorker(threading.Thread):
    '''
    DefaultScheduler working thread that dispatchs job execution
    '''
    
    def __init__(self, scheduler, name=None):
        threading.Thread.__init__(self, name=name)
        
        self.scheduler = scheduler
        
    def run(self):
        while True:
            job = self.scheduler.get_job()
            if job == self.scheduler.LAST_JOB:
                break
            
            ### TODO: Use Processor, check exceptions
            job.execute()
            
            self.scheduler.put_job(job)

class DefaultScheduler(Scheduler):
    '''
    Default implementation of the scheduler interface.
    '''
    
    # Run queue policy
    RUN_POLICY_FIFO = 1
    RUN_POLICY_LIFO = 2
    
    # Error policy
    ERROR_POLICY_IMMEDIATE = 1
    ERROR_POLICY_DELAYED = 2
    
    # Used to stop working threads
    LAST_JOB = Job()
    
    def __init__(self,
                 max_procs = 1,
                 run_policy = RUN_POLICY_FIFO,
                 error_policy = ERROR_POLICY_IMMEDIATE):
        
        self.max_procs = max_procs
        
        self.run_policy = run_policy
        
        self.error_policy = error_policy
        
        self._running_jobs = []
        
        self._waiting_jobs = []
        
        self._jobs = []
        
        self._jobs_cond = threading.Condition()
        
        self._workers = []

    def schedule(self, tasks):
        self._jobs_cond.acquire()
        self._invoke(tasks)
        self._jobs_cond.release()
        
    def run(self, tasks = []):
        self.schedule(tasks)
        
        self._workers = []
        for i in range(self.max_procs):
            worker = DefaultSchedulerWorker(scheduler = self, 
                                            name="sched_worker_" + str(i))
            self._workers.append(worker)
            worker.start()
            
        for worker in self._workers:
            worker.join()
    
    # TODO: Empty the queues
    def stop(self):
        self._jobs_cond.acquire()
        self._invoke([self.LAST_JOB])
        self._jobs_cond.release()
    
    def get_job(self):
        self._jobs_cond.acquire()
        job = None
        while job is None:
            if self._no_jobs():
                job = self.LAST_JOB
            else:
                if len(self._running_jobs) == 0:
                    self._jobs_cond.wait()
    
                if len(self._running_jobs) != 0:
                    if self.run_policy == DefaultScheduler.RUN_POLICY_FIFO:
                        job = self._running_jobs.pop(0)
                    elif self.run_policy == DefaultScheduler.RUN_POLICY_LIFO:
                        job = self._running_jobs.pop()
                    else:
                        raise Exception("Unknown run queue policy: " + self.run_policy)

        self._jobs_cond.release()
        return job
    
    def put_job(self, job):
        self._jobs_cond.acquire()
        if job.status == Job.STATUS_ACTIVATION:
            self._add_running_job(job)
        elif job.status == Job.STATUS_DEP_WAITING:
            self._invoke(job.dependencies, job)
            self._add_waiting_job(job)
        elif job.status == Job.STATUS_EXECUTION:
            self._add_running_job(job)
        elif job.status == Job.STATUS_INVOCATION:
            self._add_running_job(job)
        elif job.status == Job.STATUS_TERMINATION:
            self._notify_termination(job)
            self._invoke(job.invocations)
            self._remove_job(job)
        elif job.status == Job.STATUS_NOT_ACTIVATED:
            self._notify_termination(job)
            self._remove_job(job)
        else:
            raise NotImplemented("put_job: " + Job.status_str[job.status])
        self._jobs_cond.release()
    
    ### Running jobs management
    
    def _add_running_job(self, job):
        self._running_jobs.append(job)
        self._jobs_cond.notify()
    
    # TODO: remove ? use in get_job ?
    def _get_running_job(self):
        if len(self._running_jobs) == 0:
            self._jobs_cond.wait()

        if self.run_policy == DefaultScheduler.RUN_POLICY_FIFO:
            return self._running_jobs.pop(0)
        elif self.run_policy == DefaultScheduler.RUN_POLICY_LIFO:
            return self._running_jobs.pop()
        else:
            raise Exception("Unknown run queue policy: " + self.run_policy)
    
    ### Waiting jobs management
    
    def _add_waiting_job(self, job):
        self._waiting_jobs.append(job)
        
    def _remove_waiting_job(self, job):
        self._waiting_jobs.remove(job)
        
    ### Tasks management (callers are responsible for locking)
    
    def _find_job_by_task(self, task):
        for job in self._jobs:
            if job.task == task:
                return job
            
        return None
    
    def _create_job(self, task, status = Job.STATUS_ACTIVATION):
        job = Job(task, status)
        self._jobs.append(job)
        self._jobs_cond.notify()
        return job
    
    def _remove_job(self, job):
        self._jobs.remove(job)
        self._jobs_cond.notify()
    
    def _invoke(self, tasks, wjob = None):
        for task in tasks:
            job = self._find_job_by_task(task)
            if job is None:
                job = self._create_job(task)
                self._add_running_job(job)
            
            if wjob is not None:
                job.add_waiting_job(wjob)
    
    def _notify_termination(self, job):
        wjobs = job.get_waiting_jobs()
        for wjob in wjobs:
            wjob.notify_termination(job)
            if not wjob.is_waiting():
                self._remove_waiting_job(wjob)
                if wjob.status == Job.STATUS_DEP_WAITING:
                    wjob.status = Job.STATUS_EXECUTION
                    self._add_running_job(wjob)
                else:
                    raise NotImplemented("_notify_termination: " + Job.status_str[wjob.status])

    def _no_jobs(self):
        return len(self._jobs) == 0 \
                and len(self._running_jobs) == 0 \
                and len(self._waiting_jobs) == 0
