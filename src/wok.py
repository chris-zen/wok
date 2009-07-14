'''
Created on 28/06/2009

@author: chris
'''

from optparse import OptionParser

import logging

from wok.workflow import Workflow
from wok.scheduler import DefaultScheduler

from string import *

def execfile(file, globals=globals(), locals=locals()):
    fh = open(file, "r")
    src_code = fh.read()+"\n"
    fh.close()
    compiled_code = compile(src_code, file, 'exec') 
    exec(compiled_code, globals, locals)

def main():
    version = "%prog 1.0"
    usage = "usage: %prog [options] tasks"
    parser = OptionParser(usage=usage, version=version)

    # Logger
    
    parser.add_option("-l", "--logger", dest="logger", 
                      default="std", choices=["std", "http"], 
                      help="Which logger to use: std, http")
    
    parser.add_option("-L", "--log-level", dest="log_level", 
                      default="info", choices=["debug", "info", "warn", "error", "critical", "notset"], 
                      help="Which log level: debug, info, warn, error, critical, notset")
    
    # Scheduling
    
    parser.add_option("-j", "--max-procs", type="int", dest="max_procs", default="1",
                      help="Maximum number of processors allowed. 0 to specify all which are available.")
    
    parser.add_option("--run-policy", dest="run_policy",
                      default="fifo", choices=["fifo", "lifo"],
                      help="Run queue policy: fifo, lifo.")

    parser.add_option("--error-policy", dest="error_policy",
                      default="immediate", choices=["immediate", "delayed"],
                      help="On error termination policy: immediate, delayed.")
    
    # Task files
    
    parser.add_option("-t", "--tasks", dest="task_files",
                      action="append", default=None,
                      help="File containing Task definitions.")
    
    (opts, args) = parser.parse_args()
    
    parser.destroy()
    
    # Initialize logging
    
    logging.basicConfig()
    logger = logging.getLogger("")
    level = logging.INFO
    if upper(opts.log_level) == "DEBUG":
        level = logging.DEBUG
    elif upper(opts.log_level) == "INFO":
        level = logging.INFO
    elif upper(opts.log_level) == "WARN":
        level = logging.WARN
    elif upper(opts.log_level) == "ERROR":
        level = logging.ERROR
    elif upper(opts.log_level) == "CRITICAL":
        level = logging.CRITICAL
    elif upper(opts.log_level) == "NOTSET":
        level = logging.NOTSET
    logger.setLevel(level)
    
    log = logging.getLogger("wok-cli")
    
    # Initialize scheduler
    
    scheduler = DefaultScheduler()
    
    scheduler.max_procs = opts.max_procs
    
    if lower(opts.run_policy) == "fifo":
        scheduler.run_policy = DefaultScheduler.RUN_POLICY_FIFO
    elif lower(opts.run_policy) == "lifo":
        scheduler.run_policy = DefaultScheduler.RUN_POLICY_LIFO
    else:
        raise Exception("Unknown run policy: " + opts.run_policy)
    
    if lower(opts.error_policy) == "immediate":
        scheduler.error_policy = DefaultScheduler.ERROR_POLICY_IMMEDIATE
    elif lower(opts.error_policy) == "delayed":
        scheduler.error_policy = DefaultScheduler.ERROR_POLICY_DELAYED
    else:
        raise Exception("Unknown error policy: " + opts.error_policy)

    # Initialize tasks
    
    import os.path
    
    if opts.task_files is None:
        opts.task_files = ["tasks.py"]
    
    for task_file in opts.task_files:
        log.debug("Loading task definitions from " + task_file + " ...")
        
        if not os.path.exists(task_file):
            raise Exception("Task definition file not found: " + task_file)

        execfile(task_file)
    
    tasks = []
    for task_def in args:
        log.debug("Evaluating " + task_def + " ...")
        try:
            task = eval(task_def)
            if not isinstance(task, Task):
                raise Exception("Argument doesn't evaluate to a Task: " + task_def)
        except:
            raise Exception("Error evaluating task: " + task_def)
        tasks.append(task)
    
    # Initialize workflow
    
    log.debug("Running workflow ...")
    
    wf = Workflow()
    wf.scheduler = scheduler
    wf.run(tasks)
    
if __name__ == '__main__':
    main()