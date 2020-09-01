# -*- coding: utf-8 -*-
"""
@date Fri Jul 31 13:59:39 2020

@brief Schedule class for holding tasks

@author: aweis
"""

import datetime
import json

#libs for exporting
try:
    import plotly.express as px #REQUIRES PLOTLY 4.9 or ABOVE
except ModuleNotFoundError:
    print("Plotly Not Available")
    
try:
    import xlsxwriter
except ModuleNotFoundError:
    print("XslxWriter Not Available (no Excel capability)")


from pyschedule.Tasks import Task, Dependency

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

    def plot_plotly(self,level=0,**kwargs):
        '''@brief plot the gantt chart with plotly'''
        t0 = self.tasks
        tasks = []
        if level>0:
            for l in range(level):
                lt = []
                for t in t0:
                    lt+= t['children']
                tasks = lt
        if level<0:
            for t in t0:
                tasks.append(t)
                tasks += t._unpack_children()
        info_lists = self._get_as_lists(tasks)
        names = self._get_label_names(info_lists['nickname'],info_lists['name'])
        fig = px.timeline(x_start=info_lists['start'],x_end=info_lists['end'], 
                          y=names, color=info_lists['percent_complete'])
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            shapes=[dict(x0=datetime.datetime.today(),
                         x1=datetime.datetime.today(),
                         y0=0,y1=1,xref='x',yref='paper',line_width=2)],
            annotations=[dict(x=datetime.datetime.today(), y=1.1, xref='x',
                              yref='paper',font=dict(color="black",size=14),
                              showarrow=False, xanchor='left', 
                              text='Today ({})'.format(datetime.datetime.today()))]
            )
        
        return fig
    
    def plot_excel(self,fpath,**kwargs):
        '''
        @brief create a gantt chart from an excel spreadsheet
        @param[in] fpath - path to file to write spreadsheet to
        '''
        wb = xlsxwriter.Workbook(fpath)
        ws = workbook.add_worksheet()
        row=0; col=0
        for task in self.tasks:
            ws.write(row,col,task.nickname) 
            row+=1
            
            
        
        
            
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


     