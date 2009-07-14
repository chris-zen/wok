
import wok.shell

def run(file, args = None, cmd = "R", log=None):
    options = "--vanilla --slave -f " + file
    if args is not None:
        options += " --args " + args

    return wok.shell.run(cmd + " " + options, log=log)