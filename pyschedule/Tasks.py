# -*- coding: utf-8 -*-
"""
@date Thu Jul 30 14:26:20 2020

@brief Information about this Module

@author: aweis
"""

import datetime
import numpy as np

class Task(dict):
    '''
    @brief implementation of a Task in a schedule
    @param[in] name - name of the task is required
    @note all date/times are datetime.datetime objects or
        in the format '%Y-%m-%d %H:%M:%S.%f'
    @note 2 of the three (start/end/duration) can be specified
        when there are no dependencies
    @param[in/OPT] kwargs - keyword arguments as follows
        - start - start date/time 
        - end   - end date/time
        - duration - duration in datetime.timedelta or '%d days, %H:%M:%S'
        - dependencies = [list of Dependency Objects]
        - progress - {percent:(0-100),notes: what the progress is}
        - risks - [{percent:possibility of failure(0-100),notes: whats the risk}]
        - children - [list of Tasks that are part of this task]
        - todo - [list of Task objects that need to be completed]
        - deliverables - [list of deliverables that will come out of this task]
        - contributions - [what contributions these tasks will provide]
        - resources - [list of Resources that this requires]
    '''
    def __init__(self,name:str,start:datetime.datetime=None,end:datetime.datetime=None,
                 duration:datetime.timedelta=None,**kwargs):
        '''@brief constructor'''
        super().__init__({'name':name,'start':start,'end':end,'duration':duration})
        # add our defaults
        defaults = {
            'dependencies':[],
            'children':[],
            'progress':{'percent':0,'notes':None},
            'risks': [],
            'todo': [],
            'deliverables': [],
            'contributions': [],
            'resources': [],
            }
        self.update(defaults)
        #update from inputs
        self.update(kwargs)
        
    def add_dependency(self,dep,update=True):
        '''@brief add a dependency object to the task'''
        self['dependencies'].append(dep)
        if update: #update our dates when a dependency is added
            self.update_from_dependencies()
        
    def update_from_dependencies(self,verify=True):
        '''@brief update times based on dependencies'''
        dep_times = {'start':None,'end':None,'duration':None}
        dvals = {}
        for d in self['dependencies']:
            dvals.update(d.get_dependency())
        self.update(dvals)
        if verify: #verify our times
            self.verify()
            
    def verify(self):
        '''@brief verify the task times are not overdefined'''
        sed_vals = [self.get(k,None) for k in ['start','end','duration']]
        num_nuns = len([v for v in sed_vals if v is None]) #number of None values
        if num_nuns > 1: 
            raise Exception("Underdefined times, this could be due to not updating dependencies.")
        if num_nuns < 1:
            raise Exception("Overdefined times, Start/End/Duration cannot all be defined.")
        
    # properties to return times if not provided
    @property
    def start(self):
        '''@brief return the start datetime'''
        start = self.get('start',None)
        if start is None:
            start = self.end-self.duration
        return start 
    @property
    def end(self):
        '''@brief return end datetime'''
        end = self.get('end',None)
        if end is None:
            end = self.start+self.duration
        return end
    @property
    def duration(self):
        '''@brief return duration timedelta'''
        dur = self.get('duration',None)
        if dur is None:
            dur = self.end-self.start
        return dur
    
    def __str__(self):
        '''@brief return name for string'''
        return self['name']

class Dependency(dict):
    '''
    @brief dependencies tasks may have on one another
    @param[in] dep_task - task object to be dependent on
    @param[in] dep_type - type of dependency. Can be any of the following:
        - startsBefore - Must start before the dep_name task begins
        - startsWith   - Must start at the same time as dep_name task
        - startsAfter  - Must start after dep_name task is over
        - endsBefore   - Must end before dep_name starts
        - endsWith     - Must end at the same time as dep_name
        - endsAfter    - Must end after dep_name ends
    @note the most likely type will be startsAfter
    '''
    def __init__(self,dep_task:Task,dep_type:str):
        '''@brief constructor'''
        allowed_types = ['startsBefore','startsWith','startsAfter',
                         'endsBefore'  ,'endsWith'  ,'endsAfter'  ]
        if dep_type not in allowed_types:
            raise Exception("{} is not an allowable type of dependency".format(dep_type))
        super().__init__(task=dep_task,type=dep_type)
    
    def get_dependency(self):
        '''@brief get a dependency time given a task'''
        return getattr(self,'_'+self['type'])(self['task']);
    
    def _startsBefore(self,task):
        '''@brief calculate date on startsBefore'''
        return {'start':task.start}
    def _startsWith(self,task):
        '''@brief calculate date on startsWith'''
        return {'start':task.start}
    def _startsAfter(self,task):
        '''@brief calculate date on startsBefore'''
        return {'start':task.end}
    def _endsBefore(self,task):
        '''@brief calculate date on endsBefore'''
        return {'end':task.start}
    def _endsWith(self,task):
        '''@brief calculate date on endsWith'''
        return {'end':task.end}
    def _endsAfter(self,task):
        '''@brief calculate date on endsAfter'''
        return {'end':task.end}
    
#%% Unit testing

import unittest

class TestTasks(unittest.TestCase):
    start_datetime = datetime.datetime.today()
    start_duration = datetime.timedelta(days=7)
    task_len_days = [1,10,150,27,4]
    time_deltas = [datetime.timedelta(days=d) for d in task_len_days]
    
    def test_cascaded_tasks(self):
        '''@brief test each task starting after the other'''
        start_task = Task('task_start',start=self.start_datetime,duration=start_duration)
        other_tasks = [Task('task_{}'.format(i),duration=td) for i,td in enumerate(self.time_deltas)]

if __name__=='__main__':
    
    t1 = Task('task1',start=datetime.datetime.today()
              ,duration=datetime.timedelta(days=7))
    t2 = Task('task2',duration=datetime.timedelta(days=14))
    t3 = Task('task3',duration=datetime.timedelta(days=31))
    
    t2.add_dependency(Dependency(t1,'startsAfter'))
    t3.add_dependency(Dependency(t2,'startsAfter'))
    


