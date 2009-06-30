'''
Created on 30/06/2009

@author: chris
'''

class Job():
    
    # Maximum number of jobs allowed in parallel
    max_parallel = 0
    
    # Minimum required memory
    min_memory = 0
    
    def __init__(self, **attrs):
        self.__dict__.update(attrs)
    
    def activate(self):
        return True;
    
    def dependencies(self):
        return []
    
    def execute(self):
        pass
        
    def invokes(self):
        pass

