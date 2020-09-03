# -*- coding: utf-8 -*-
"""
@date Thu Sep  3 10:30:27 2020

@brief IO for reading/writing from microsoft office formats

@author: aweis
"""

import copy
import numpy as np

try:
    import openpyxl
except ModuleNotFoundError:
    print("Cannot import OpenPyxl (no Excel capability). Try `pip install openpyxl`.")
    
from ..Tasks import unpack_children_with_levels
from ..Schedule import Schedule,get_range_ymd,get_datetime_range

#%% Write schedule to excel

def write_excel(schedule:Schedule,fpath:str,**kwargs):
    '''
    @brief create a gantt chart from an excel spreadsheet
    @param[in] schedule - schedule to write out
    @param[in] fpath - path to file to write spreadsheet to
    '''
    wb = openpyxl.Workbook()
    ws = wb.active
    
    # Lets first load everything so we know the sizes of tasks, times, etc
    ## Load our tasks
    tasks,levels = unpack_children_with_levels(schedule,-1)
    task_levels = max(levels)-min(levels)+1
    ## Now get date/time range 
    years,months,days = get_range_ymd(schedule.start, schedule.end)
    date_range = get_datetime_range(schedule.start,schedule.end)
    time_cols = np.size(months)
    
    # Set up the formatting
    ## Header Formatting
    #head_fmt = wb.add_format({'bold':True,'align':'center'})
    ## Task formatting
    #task_col_fmt = wb.add_format({'text_wrap':True})
    ## Date Header Formatting
    #date_head_fmt = head_fmt
    
    # Now lets set the sizes of everything
    ## Our header
    head_row_start = 1; 
    head_col_start = 1
    head_rows = 2; 
    head_cols = task_levels 
    head_row_end = head_row_start+head_rows-1
    head_col_end = head_col_start+head_cols-1
    ## Our tasks
    task_row_start = head_row_start+head_rows;
    task_col_start = 1
    task_rows = len(tasks)
    task_cols = task_levels 
    task_row_end = task_row_start+task_rows-1
    task_col_end = task_col_start+task_cols-1
    ## Date header
    date_head_row_start = 1
    date_head_col_start = head_col_end+1
    date_head_rows = head_rows 
    date_head_cols = sum([len(month) for month in months])
    ## Date range
    date_range_row_start = date_head_row_start+date_head_rows
    date_range_col_start = date_head_col_start 
    date_range_rows = task_rows
    date_range_cols = date_head_cols
    ## Totals
    total_row_start = 1
    total_col_start = 1
    total_rows = head_rows+task_rows
    total_cols = date_head_col_start+date_head_cols
    total_row_end = total_row_start+total_rows-1
    total_col_end = total_col_start+total_cols-1
    
    # now write out values
    ## Write our header
    ws.cell(row=head_row_start,column=head_col_start,value="Tasks")
    ## Write our date header
    date_head_col = date_head_col_start; date_head_row = date_head_row_start
    for yi,y in enumerate(years):
        ws.cell(row=date_head_row,column=date_head_col,value=y)
        ws.merge_cells(start_row=date_head_row,start_column=date_head_col,
                       end_row=date_head_row,end_column=date_head_col+len(months[yi])-1)
        month_col = date_head_col
        for month in months[yi]:
            ws.cell(row=date_head_row+1,column=month_col,value=month)
            month_col += 1
        date_head_col += len(months[yi])
    ## Write out our tasks
    task_row=task_row_start; task_col=task_col_start
    for t,l in zip(tasks,levels):
        mycell = ws.cell(row=task_row,column=task_col+l,value=t.nickname)
        mycell.alignment = openpyxl.styles.Alignment(wrap_text=True)
        print(' '*2*l+t['name'])
        task_row += 1
    for c in range(task_col_start,task_col_end+1): 
        ws.column_dimensions[openpyxl.utils.get_column_letter(c)].width = 20
        
    # Now shade the columns for the tasks
    ym = [date.strftime('%Y-%m') for date in date_range]
    ymu = np.unique(ym)
    for task_row,t in enumerate(tasks):
        td_range = get_datetime_range(t.start,t.end)
        tdu_range = np.unique([date.strftime('%Y-%m') for date in td_range])
        trows = [date_range_row_start+task_row]
        tcols = [date_range_col_start+np.where(ymu==tdu)[0][0] for tdu in tdu_range]
        for r in trows:
            for c in tcols:
                cell = ws.cell(row=r,column=c)
                shading = openpyxl.styles.PatternFill("solid", fgColor="88888888")
                cell.fill = shading
                
    
    # Draw our borders but dont change other formatting
    thick_border = openpyxl.styles.Side(border_style="thick", color="000000")
    ## Bottom borders
    bb_rows = [head_row_end,total_row_end]+list(task_row_start-1+np.where(np.array(levels)==0)[0])
    bb_cols = range(total_col_start,total_col_end)
    for r in bb_rows:
        for c in bb_cols:
            cell = ws.cell(row=r,column=c)
            myborder = copy.copy(cell.border)
            myborder.bottom = thick_border
            cell.border = myborder
    # Right borders
    br_cols = [task_col_end]+list(date_head_col_start-1+np.cumsum([len(m) for m in months]))
    br_rows = range(total_row_start,total_row_end+1)
    for r in br_rows:
        for c in br_cols:
            cell = ws.cell(row=r,column=c)
            myborder = copy.copy(cell.border)
            myborder.right = thick_border
            cell.border = myborder
    
    # finally save it out
    wb.save(filename = fpath)