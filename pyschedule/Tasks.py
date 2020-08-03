# -*- coding: utf-8 -*-
"""
@date Thu Jul 30 14:26:20 2020

@brief Information about this Module

@author: aweis
"""

import datetime

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
        - dependendencies = [list of Dependency Objects]
        - progress - {percent:(0-100),notes: what the progress is}
        - risks - [{percent:possibility of failure(0-100),notes: whats the risk}]
        - children - [list of Tasks that are part of this task]
        - todo - [names of subtasks that need to be completed]
        - deliverables - [list of deliverables that will come out of this task]
        - contributions - [what contributions these tasks will provide]
        - resources - [list of Resources that this requires]
    '''
    def __init__(self,name,**kwargs):
        '''@brief constructor'''
        super().__init__({'name':name})
    

class Dependency(dict):
    '''
    @brief dependencies tasks may have on one another
    @param[in] dep_name - name of Task that we are dependent on
    @param[in] dep_type - type of dependency. Can be any of the following:
        - startsBefore - Must start before the dep_name task begins
        - startsWith   - Must start at the same time as dep_name task
        - startsAfter  - Must start after dep_name task is over
        - endsBefore   - Must end before dep_name starts
        - endsWith     - Must end at the same time as dep_name
        - endsAfter    - Must end after dep_name ends
    @note the most likely type will be startsAfter
    '''
    def __init__(self,dep_name,dep_type):
        '''@brief constructor'''
        allowed_types = ['startsBefore','startsWith','startsAfter',
                         'endsBefore'  ,'endsWith'  ,'endsAfter'  ]
        if dep_type not in allowed_types:
            raise Exception("{} is not an allowable type of dependency".format(dep_type))
        super().__init__(name=dep_name,type=dep_type)
    
    def get_dependency(self,task):
        '''@brief get a dependency time given a task'''
        return getattr('_'+self['type'])(task);
    
    def _startsBefore(self,task):
        '''@brief calculate date on startsBefore'''
        return {'start':task['start'],'end':None,'duration':None}
    def _startsWith(self,task):
        '''@brief calculate date on startsWith'''
        return {'start':task['start'],'end':None,'duration':None}
    def _startsAfter(self,task):
        '''@brief calculate date on startsBefore'''
        return {'start':task['end'],'end':None,'duration':None}
    def _endsBefore(self,task):
        '''@brief calculate date on endsBefore'''
        return {'start':None,'end':task['start'],'duration':None}
    def _endsWith(self,task):
        '''@brief calculate date on endsWith'''
        return {'start':None,'end':task['end'],'duration':None}
    def _endsAfter(self,task):
        '''@brief calculate date on endsAfter'''
        return {'start':None,'end':task['end'],'duration':None}



