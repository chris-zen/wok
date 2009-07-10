
from wok.workflow import Workflow

import logging
import os

__config = None

__workflow = None

def init():
    logging.basicConfig()
    root_logger = logging.getLogger("")
    root_logger.setLevel(logging.DEBUG)
    root_logger.info("wok initialized.")

def create_workflow(**args):
    return Workflow(**args)

def workflow():
    global __workflow
    
    if __workflow is None:
        __workflow = Workflow()

    return __workflow

def load_config(file):
    __config = __import__(file)
    return __config

def set_config(config):
    global __config
    __config = config
    
def config():
    return __config

def logger(name):
    return logging.getLogger(name)

def makedirs(path, mode=0777):
    try:
        os.makedirs(path, mode)
    except:
        pass
