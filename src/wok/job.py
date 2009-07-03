'''
Created on 30/06/2009

@author: chris
'''

class Job():
    
    # Maximum number of jobs allowed in parallel
    max_parallel = 0
    
    # Minimum required memory
    min_memory = 0
    
    def __init__(self, *args, **nargs):
        self.args = args
        self.nargs = {}
        self.nargs.update(nargs)
    
    def activate(self):
        return True;
    
    def dependencies(self):
        return []
    
    def execute(self):
        pass
        
    def invokes(self):
        pass

    def __eq__(self, other):
        return self.args == other.args and self.nargs == other.nargs

    def __ne__(self, other):
        return self.args != other.args or self.nargs != other.nargs
