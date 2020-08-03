# -*- coding: utf-8 -*-
"""
@date Fri Jul 31 13:59:39 2020

@brief Schedule class for holding tasks

@author: aweis
"""
from pyschedule.Tasks import Task

class Schedule(dict):
    '''
    @brief class to hold a list of tasks along with 
        metadata for a schedule
    @param[in] args - variable input arguments can be 
        of the following types:
            - Tasks - multiple inputs of Task type to put in a schedule
            - List - list of type(Task) to put into a schedule
            - Schedule - a dict of type schedule to initialize
            - String - a path to a schedule to load in
    @param[in/OPT] kwargs - key/value pairs to be added as metadata
    '''
    def __init__(*args,**kwargs):
        if isinstance(args[0],Schedule): #instantiate as a class
            super().__init__(Schedule,**kwargs)
        else:
            self['tasks'] = []
            if isinstance(args[0],list):
                for t in args[0]:
                    self.add_task(t)
            elif isinstance(args[0],Task):
                self.add_task(args[0])
            else:
                raise TypeError("Unsupported input arguments")
            
    def add_task(task,**kwargs):
        '''
        @brief add a Task to the schedule
        @param[in] task - Task to add to theschedule
        @param[in] kwargs - key/value pairs
        @note, this adds the task to the list at
        '''
        if not isinstance(task,Task):raise TypeError
        self['tasks'].append(task)
        
            
            