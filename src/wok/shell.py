import subprocess

class ShellException(Exception):
    def __init__(self, kwargs):
        self.__dict__.update(kwargs)
    
    def __str__(self):
        return self.command + "\n" + self.error

def run(command, input=None, cwd=None, env=None, check_returncode=True,
        log=None, log_cmd=True, log_out=True, log_err=True):
    
    p = subprocess.Popen(args=command, 
                         stdin=subprocess.PIPE, 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         shell=True, cwd=cwd, env=env)
    
    if log_cmd and log is not None:
        log.info(command)

    (output, error) = p.communicate(input)
    
    if log is not None:
        if log_out and output is not None and len(output) > 0: log.info(output)
        if log_err and error is not None and len(error) > 0: log.error(error)
    
    ret = { "command" : command, "returncode" : p.returncode,
            "input" : input, "output" : output, "error" : error }
    
    if check_returncode and p.returncode != 0:
        raise ShellException(ret)
    
    return ret
