# -*- coding: utf-8 -*-
"""
@date Thu Sep  3 11:14:08 2020

@brief Information about this Module

@author: aweis
"""

import datetime

try:
    import plotly.express as px #REQUIRES PLOTLY 4.9 or ABOVE
except ModuleNotFoundError:
    print("Plotly Not Available")

from ..Schedule import Schedule

def plot_plotly(schedule:Schedule,level:int=0,**kwargs):
    '''@brief plot the gantt chart with plotly'''
    t0 = schedule.tasks
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
    info_lists = schedule._get_as_lists(tasks)
    names = schedule._get_label_names(info_lists['nickname'],info_lists['name'])
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