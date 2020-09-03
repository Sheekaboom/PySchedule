# -*- coding: utf-8 -*-
"""
@date Fri Jul 31 13:59:39 2020

@brief Schedule class for holding tasks

@author: aweis
"""

import datetime
import json
import numpy as np

from pyschedule.Tasks import Task, Dependency

#%% Some extended datetime functionality

def get_datetime_range(start:datetime.datetime,stop:datetime.datetime,delta:datetime.timedelta=datetime.timedelta(days=1)):
    '''
    @brief get a list of datetime.datetime objects from
        start to stop with change delta (includes the end time)
    @param[in] start - start datetime.datetime object
    @param[in] stop - stop datetime.datetime.object
    @param[in] delta - datetime.timedelta object for step
    '''
    date_range = np.arange(start,stop+delta,delta)
    dates = np.unique(np.datetime_as_string(date_range,'D')) #unique year/months
    dtdates = [datetime.datetime.strptime(date,'%Y-%m-%d') for date in dates] #change to datetime objects
    return dtdates

def get_range_ymd(start:datetime.datetime,stop:datetime.datetime):
    '''
    @brief get years, months, and days from a range of start/stop dates
    @return [y1,y2],[[m1y1,m2y1,m3y1,...],[m1y2,m2y2,m3y2,...]],[[[m1y1d1,...],[m2y1d1,...]],][[m1y2d1,...],[m2y2d1,...]],...]
        (e.g. year=years[yi] month=months[yi][mi] day=days[yi][mi][di])
    '''
    dtdates = get_datetime_range(start,stop,datetime.timedelta(days=1))
    years = np.unique([date.year for date in dtdates]) #get unique years
    year_split = [[date for date in dtdates if date.year==year] for year in years]
    months = [np.unique([date.month for date in year]) for year in year_split]
    months_str = [[datetime.datetime(1,m,1).strftime('%b') for m in ymonths] for ymonths in months]
    month_split = [[[date for date in year if date.month==month] for month in months[yi]] for yi,year in enumerate(year_split)]
    days = [[[day.strftime('%d') for day in month] for month in year] for year in month_split]
    return years,months_str,days


#%% now our schedule class

class Schedule(Task):
    '''
    @brief class to hold a list of tasks along with 
        metadata for a schedule
    @param[in] name - name of the Schedule
    @param[in] args - variable input arguments can be 
        of the following types:
            - Tasks - multiple inputs of Task type to put in a schedule
            - List - list of type(Task) to put into a schedule
            - Schedule - a dict of type schedule to initialize
            - String - a path to a schedule to load in
    @param[in/OPT] kwargs - key/value pairs to be added as metadata
    '''
    def __init__(self,name,*args,**kwargs):
        super().__init__(name,**kwargs)
        if len(args):
            if isinstance(args[0],Schedule): #instantiate as a class
                self.update(Schedule)
            else:
                if isinstance(args[0],list):
                    for t in args[0]:
                        self.add_task(t)
                elif isinstance(args[0],Task):
                    self.add_task(args[0])
                else:
                    raise TypeError("Unsupported input arguments")
        self.update(kwargs)
            
    def add_task(self,task,**kwargs):
        '''
        @brief add a Task to the schedule
        @param[in] task - Task to add to the schedule
        @param[in] kwargs - key/value pairs
        @note, this adds the task to the list at
        '''
        if not isinstance(task,Task):raise TypeError
        deps = task['dependencies']
        task.verify()
        self['children'].append(task)
        
    @property
    def tasks(self):
        return self['children']
        
    def sort_tasks(self,verify=True,**kwargs):
        '''
        @brief sort tasks based on start time
        '''
        if verify: [t.verify() for t in self.tasks]
        end_sort = sorted(self.tasks,key=lambda task: task.end) # sort by end date first
        self['children'] = sorted(end_sort,key=lambda task: task.start)
        
#%% IO functionality
    
    def load(self,fname):
        '''
        @brief load schedule from a json file
        @param[in] fpath - path to json file to load
        '''
        with open(fname,'r') as fp:
            json_data = json.load(fp, kwds)
        
    
#%% Export functionality
    def _get_as_lists(self,tasks):
        '''
        @brief get fields from the schedule as lists. Typically useful for exporting/plotting
        @return dict('name':[names],'start':[task.start],'end':[task.end],
                     'percent_complete':[task['progress']['percent']])
        '''
        rd = {}
        rd['name'] = [task['name'] for task in tasks]
        rd['nickname'] = [task.get('nickname',None) for task in tasks]
        rd['start'] = [task.start for task in tasks]
        rd['end'] = [task.end for task in tasks]
        rd['percent_complete'] = [task.progress['percent'] for task in tasks]
        return rd
    
    def _get_label_names(self,nicknames,names):
        '''@brief use nicknames when available otherwise use full name'''
        label_names = []
        for i,n in enumerate(nicknames):
            if n in [None,'','None']:
                label_names.append(names[i])
            else:
                label_names.append(n)
        return label_names
            
        
            
#%% Testing
import unittest

class TestSchedule(unittest.TestCase):
    '''@brief test scheduling things'''
    pass

if __name__=='__main__':

    t1 = Task('task1',start=datetime.datetime.today()-datetime.timedelta(days=5)
              ,duration=datetime.timedelta(days=7))
    t2 = Task('task2',duration=datetime.timedelta(days=14))
    t3 = Task('task3',duration=datetime.timedelta(days=31))
    t4 = Task('task3',duration=datetime.timedelta(days=31))
    
    t2.add_dependency(Dependency(t1,'startsAfter'))
    t3.add_dependency(Dependency(t1,'startsAfter'))

    mySchedule = Schedule('PhD Roadmap',[t1,t2,t3])
    fig = mySchedule.plot_plotly()
    fig.show(renderer='svg')


     