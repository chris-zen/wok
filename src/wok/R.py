
from wok.shell import *

def run(file, args = None, cmd = "R", log=None):
    options = "--vanilla --slave -f " + file
    if args is not None:
        options += " --args " + args

    return shell(cmd + " " + options, log=log)