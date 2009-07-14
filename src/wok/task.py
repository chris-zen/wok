'''
Created on 08/07/2009

@author: chris
'''

class Task(object):
    
    # Maximum number of jobs allowed in parallel
    max_parallel = 0
    
    # Minimum required memory
    min_memory = 0
    
    def __init__(self, *args, **nargs):
        self.args = list(args)
        self.nargs = dict(nargs)
    
    def name(self):
        return self.__class__.__name__
    
    def activate(self):
        return True;
    
    def dependencies(self):
        return []
    
    def execute(self):
        pass
    
    def invoke(self):
        return []

    def __eq__(self, other):
        return self.name() == other.name() \
                and self.args == other.args \
                and self.nargs == other.nargs

    def __ne__(self, other):
        return self.name() != other.name() \
                or self.args != other.args \
                or self.nargs != other.nargs

    def __repr__(self):
        sb = [self.name()]
        if self.args is not None and len(self.args) > 0:
            sb += [" ", repr(self.args)]
        if self.nargs is not None and len(self.nargs) > 0:
            sb += [" ", repr(self.nargs)]
        return "".join(sb)
