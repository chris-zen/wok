'''
Created on 29/06/2009

@author: chris
'''

class Processor(object):
    '''
    Represents an execution processor 
    and defines the interface any processor should follow
    '''

    def execute(self, job):
        raise NotImplemented("abstract method")

class DefaultProcessor(Processor):
    pass