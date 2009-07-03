'''
Created on 28/06/2009

@author: chris
'''

from wok import *
from wok.workflow import *
from wok.job import *

j1 = Job("J1")
j2 = Job("J2")

if __name__ == '__main__':
    wf = Workflow()
    wf.run(j1, j2)