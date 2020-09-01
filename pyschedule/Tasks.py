# -*- coding: utf-8 -*-
"""
@date Thu Jul 30 14:26:20 2020

@brief Information about this Module

@author: aweis
"""

import datetime
import json
import os
import numpy as np
import re
from typing import Union

#%% Some useful functions

def load_dependencies(task_list):
    '''
    @brief take a list of tasks and correlate their dependencies to the task objects
    @note any dependency should match the name of the task it depends on
    @note THIS WILL NOT VERIFY THE TASK. You should run .verify() separately
    @note this will run _unpack_children to load run for all children also
    @note non object dependencies expect {'task':task_id|task_name,'type':'startsWith'|'startsAfter'|...}
    @param[in] task_list - list of Tasks that have dependencies. All dependent tasks
        MUST be inside of this list
    @return list of Tasks with correlated object dependencies. These should also be updated in place
    '''
    if isinstance(task_list,Task): #if its a single task, make a 1 element list
        task_list = [task_list]
    tl_in = []
    for t in task_list:
        tl_in.append(t)
        tl_in += t._unpack_children()
    tl_out = []
    tl_ids = []
    for t in tl_in: #create our ids. look for 'id' input first otherwise try to match by name
        tl_ids.append(t.get('id',t.get('name',None)))
    for t in tl_in:
        for i in range(len(t['dependencies'])):
            if not isinstance(t['dependencies'][i],Dependency): #first check if its a dependency
                dep = t['dependencies'][i]
                dep_task_idx = np.where(np.array(tl_ids)==dep['task'])[0]
                if not len(dep_task_idx):
                    raise Exception("Task index is {}. This message likely means the dependency '{}' for {} wasn't found.".format(dep_task_idx,dep['task'],repr(t)))
                dep_task = tl_in[dep_task_idx[0]]
                if not dep_task:
                    raise Exception("Task '{}' not found".format(dep['task']))
                t['dependencies'][i] = Dependency(dep_task,dep['type'])
        tl_out.append(t)
    for t in task_list:
        t.update_from_dependencies(verify=False)
    return tl_out

def unpack_children_with_levels(task,level):
    '''
    @brief unpack our children along with levels recursively
    @param[in] task - task to unpack from
    @param[in] level - what level this task is on
    @return [c1task,cc1task,cc2task,c2task,cc1task],[1,2,2,1,2] (example)
    '''
    children = task['children']
    ctasks = []
    levels = []
    for child in children:#now add in our children
        cct,clev = unpack_children_with_levels(child,level+1)
        ctasks.append(child)
        ctasks += cct
        levels.append(level+1)
        levels += clev
    return ctasks,levels
    

#%% Tasks for scheduling

class Task(dict):
    '''
    @brief implementation of a Task in a schedule
    @param[in] name - name of the task is required. This could be a dict to load from a dict
        If this is a valid path, it will be loaded from a json file
    @note all date/times are datetime.datetime objects or
        in the format '%Y-%m-%d %H:%M:%S'. All timedeltas are datetime.timedelta
        objects or strings in the format '%dd%H:%M:%S'
    @note 2 of the three (start/end/duration) can be specified
        when there are no dependencies
    @param[in/OPT] kwargs - keyword arguments as follows
        - description - description of the task
        - start - start date/time 
        - end   - end date/time
        - duration - duration in datetime.timedelta or '%dd%H:%M:%S' (eg 90d0:0:0)
        - nickname - shortened name for things like plotting
        - dependencies = [list of Dependency Objects]
        - progress - {percent:(0-100),notes: what the progress is}
        - risks - [{percent:possibility of failure(0-100),notes: whats the risk}]
        - todo - [list of Task objects that need to be completed]
        - deliverables - [list of deliverables that will come out of this task]
        - contributions - [what contributions these tasks will provide]
        - resources - [list of Resources that this requires]
        - children - [list of Tasks that are part of this task]
    '''
    
    undefined_vals = [None,'','None']
    
    def __init__(self,name:Union[str,dict],start:datetime.datetime=None,end:datetime.datetime=None,
                 duration:datetime.timedelta=None,**kwargs):
        '''@brief constructor'''
        super().__init__()
        #default values
        defaults = {
            'name': name,
            'start': start,
            'end': end,
            'duration': duration,
            'dependencies':[],
            'children':[],
            'progress':{'percent':None,'notes':None},
            'risks': [],
            'todo': [],
            'deliverables': [],
            'contributions': [],
            'resources': [],
            'nickname':None
            }
        self.update(defaults)
        #load from dict if name is dict
        if isinstance(name,dict):
            self.update(name)
        elif os.path.exists(name):
            with open(name) as fp:
                json_data = json.load(fp)
            self.update(json_data)
        #update from inputs
        self.update(kwargs)
        #make sure all times are converted to datetime objects
        self._load_datetimes()
        #ensure children are tasks
        for i,task in enumerate(self['children']):
            if not isinstance(task,Task):
                self['children'][i] = Task(task)
                
    @staticmethod
    def load(fpath):
        '''
        @brief load a task from a json file
        @param[in] fpath - file path to load in
        @todo allowing for saving and loading of dependencies
        @return Task Object
        @example Task.load(fpath)
        '''
        with open(fpath,'r') as fp:
            json_data = json.load(fp)
        return Task(json_data)
                
    def _load_datetimes(self):
        '''@brief convert any datetime strings or durations to datetime objects'''
        datetime_fields = ['start','end']
        duration_fields = ['duration']
        undefined_types = [None,'','None'] #types that mean the datetime isnt provided
        # fix any datetimes into datetime objects
        for field in datetime_fields:
            if isinstance(self[field],str) and self[field] not in undefined_types:
                self[field] = datetime.datetime.strptime(self[field],'%Y-%m-%d %H:%M:%S')
        for field in duration_fields:
            if isinstance(self[field],str) and self[field] not in undefined_types:
                td = [int(v) for v in re.split('(d|:)',self[field])[::2]]
                self[field] = datetime.timedelta(days=td[0],hours=td[1],minutes=td[2],seconds=td[3])
        
    def _unpack_children(self):
        '''@brief return a recursive list of all subtasks (useful for dependencies)'''
        child_list = []
        child_list += self['children']
        for t in self['children']:
            child_list += t._unpack_children()
        return child_list
        
    def add_dependency(self,dep,update=True):
        '''@brief add a dependency object to the task'''
        self['dependencies'].append(dep)
        if update: #update our dates when a dependency is added
            self.update_from_dependencies()
        
    def update_from_dependencies(self,verify=True,update_children=True):
        '''
        @brief update times based on dependencies. Update children recursively
        @param[in/OPT] verify - run self.verify() (default True)
        @param[in/OPT] update_children - whether or not to update children
        @note this updates the parent twice to ensure that both the parent can
            depend and children and children on parent
        '''
        dep_times = {'start':None,'end':None,'duration':None}
        dvals = {}
        # update self dependencies twice to cover children depending on parent
        # and parent depending on children
        for d in self['dependencies']:
            if isinstance(d,Dependency):
                dvals.update(d.get_dependency())
            else:
                raise TypeError('Dependencies must be of type {} not {}. Running load_dependencies may be required'.format(Dependency,type(d)))
        self.update(dvals)
        #recursively update children first
        # do not verify though because children do not need to define dates
        if update_children:
            for c in self['children']:
                c.update_from_dependencies(verify=False,update_children=True)
        # update the dependencies
        for d in self['dependencies']:
            dvals.update(d.get_dependency())
        self.update(dvals)
        if verify: #verify our times
            self.verify()
            
    def verify(self,verbose=False):
        '''@brief verify the task times are not overdefined'''
        sed_vals = [getattr(self,k)(False) for k in ['get_start','get_end','get_duration']]
        num_nuns = len([v for v in sed_vals if v is None]) #number of None values
        if num_nuns < 1: 
            raise Exception("Overdefined times for '{}', Start/End/Duration cannot all be defined.".format(repr(self))+
                            " Some of these may be defined from added dependencies.\n"+
                            "    -Start    = {}\n".format(sed_vals[0])+
                            "    -End      = {}\n".format(sed_vals[1])+
                            "    -Duration = {}\n".format(sed_vals[2]))
        if num_nuns > 1:
            raise Exception("Underdefined times for '{}'. Running self.update_from_dependencies may fix this.\n".format(repr(self))+
                            "    -Start    = {}\n".format(sed_vals[0])+
                            "    -End      = {}\n".format(sed_vals[1])+
                            "    -Duration = {}\n".format(sed_vals[2]))
        if verbose: print("    -Start    = {}\n".format(sed_vals[0])+
                          "    -End      = {}\n".format(sed_vals[1])+
                          "    -Duration = {}\n".format(sed_vals[2]))
        
        
#%% Return calculated times (and properties for those values)
    def get_start(self,calc_flg):
        '''
        @brief return the start datetime
        @param[in] calc_flg - calculate from other values if not available
        @note calc_flg should be false except for top call to prevent endless loop
        '''
        #try and get from the value
        start = self.get('start',None)
        if start not in self.undefined_vals:
            return start
        #try and get from children
        child_times = [child.start for child in self['children']]
        if child_times and np.any(np.array(child_times)!=None):
            return child_times[np.argmin(child_times)]
        # try to calculate
        if calc_flg:
            end = self.get_end(False)
            dur = self.get_duration(False)
            if None not in [end,dur]:
                start = end-dur
            else:
                start = None
        return start 
    
    def get_end(self,calc_flg):
        '''
        @brief return end datetime
        @param[in] calc_flg - calculate from other values if not available
        @note calc_flg should be false except for top call to prevent endless loop
        '''
        #try and get from the value
        end = self.get('end',None)
        if end not in self.undefined_vals:
            return end
        #try and get from children
        child_times = [child.end for child in self['children'] if child.end is not None]
        if child_times:
            return child_times[np.argmax(child_times)]
        # try to calculate
        if calc_flg:
            start = self.get_start(False)
            dur   = self.get_duration(False)
            if None not in [start,dur]:
                end = start+dur
            else:
                end = None
        return end
    
    def get_duration(self,calc_flg):
        '''
        @brief return duration timedelta
        @param[in] calc_flg - calculate from other values if not available
        @note calc_flg should be false except for top call to prevent endless loop
        '''
        #try and get from the value
        dur = self.get('duration',None)
        if dur is not None:
            return dur
        # try to calculate
        if calc_flg:
            end   = self.get_end(False)
            start = self.get_start(False)
            if None not in [end,start]:
                dur = end-start
            else:
                dur = None
        return dur
    
    @property 
    def start(self): return self.get_start(True)
    @property
    def end(self): return self.get_end(True)
    @property
    def duration(self): return self.get_duration(True)
    
#%% Other calculated properties    
    @property
    def progress(self):
        '''@brief return the progress. If not defined try to average children'''
        progress_dict = self.get('progress',{'percent':None,'notes':''})
        if progress_dict['percent'] in self.undefined_vals:
            progress_dict['percent'] = np.round(np.mean([st.progress['percent'] for st in self['children']]))
            progress_dict['notes'] = '#mean([children[progress]])'
        return progress_dict
    
    @property
    def nickname(self):
        '''@brief return the nickname or name if it is none'''
        nick = self.get('nickname',None)
        if nick in self.undefined_vals:
            nick = self.get('name')
        return nick
    
    def __str__(self):
        '''@brief return name for string'''
        return self['name']
    
    def __repr__(self):
        return 'Task("{}" at {})'.format(str(self),id(self))

class TaskEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.timedelta):
            return str(obj).replace(' days, ','d')
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

#%% Dependencies
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
    def __init__(self,task:Task,type:str):
        '''@brief constructor'''
        allowed_types = ['startsBefore','startsWith','startsAfter',
                         'endsBefore'  ,'endsWith'  ,'endsAfter'  ]
        if type not in allowed_types:
            raise Exception("{} is not an allowable type of dependency".format(type))
        super().__init__(task=task,type=type)
    
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
    
    def __str__(self):
        return str({'task':str(self['task']),'type':self['type']})
    
    def __repr__(self):
        return 'Dependency({})'.format({'task':repr(self['task']),'type':self['type']})
    
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
    
    test_path = r"C:\Users\aweis\Google Drive\GradWork\PhD\schedule\tasks\ofdm_simulation.json"
    lt = Task.load(test_path)
    
    t1 = Task('task1',start=datetime.datetime.today()
              ,duration=datetime.timedelta(days=7))
    t2 = Task('task2',duration=datetime.timedelta(days=14))
    t3 = Task('task3',duration=datetime.timedelta(days=31))
    
    t4 = Task('task4',duration=datetime.timedelta(days=20),dependencies=[{'task':'task2','type':'startsAfter'}])
    
    t5 = Task(
            {
                "name":"task5",
                "start":"2020-05-05 0:0:0",
                "children":[
                    {"name": "task05","duration":"7d0:0:0","dependencies":[{"task":"task5","type":"startsWith"}]},
                    {"name": "task15","duration":"7d0:0:0","dependencies":[{"task":"task05","type":"startsAfter"}]},
                    {"name": "task25","duration":"7d0:0:0","dependencies":[{"task":"task15","type":"startsAfter"}]},
                    {"name": "task35","duration":"7d0:0:0","dependencies":[{"task":"task25","type":"startsAfter"}]}
                    ]}
        )
    load_dependencies(t5)
    
    tpar = Task('parent',children=[t5,t4])
    
    tunder = Task('Underdefined',duration=datetime.timedelta(days=14))
    #tunder.verify()
    tover = Task('Overdefined',start=datetime.datetime.today(),end=datetime.datetime.today(),duration=datetime.timedelta(days=10))
    #tover.verify()
    
    t2.add_dependency(Dependency(t1,'startsAfter'))
    t3.add_dependency(Dependency(t2,'startsAfter'))
    
    tl = load_dependencies([t4,t3,t2])
    
    
    
    


