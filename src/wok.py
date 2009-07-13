'''
Created on 28/06/2009

@author: chris
'''

from optparse import OptionParser

import logging

from wok.workflow import Workflow
from wok.scheduler import DefaultScheduler
from wok.processor import DefaultProcessor

def main():
    version = "%prog 1.0"
    usage = "usage: %prog [options] jobs"
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
    
    (opts, args) = parser.parse_args()
    
    parser.destroy()
    
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
        
    processor = DefaultProcessor()
    
if __name__ == '__main__':
    main()