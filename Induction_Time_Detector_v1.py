# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 13:50:18 2019

@author: Antony Vassileiou


GOAL
To determine the induction time for each temperature cycle in the supplied Crystalline raw data.
This is achieved by identifying 2 points, A and B, such that:
A = the FIRST point where the temperature has stabilised at the low setting with transmissivity still high
B = the LAST point where the transmissivity is high before dropping low whilst the temperature remains low
Various parameters are specified to control the precise definitions of "high", "low", etc.

ASSUMPTIONS
1. Maximum temperature reached in experiment is > 20degC
2. Both maximum and minimum temperature are constant over each temperature cycle

OUTPUTS
1. A text file containing the numbers for each induction time.
2. An interactive plot of the traces in the file, with detected induction times marked.  Open with any browser.
   ### Do check this: it is your best chance to see what the code has done and catch anything that's gone wrong.

REQUIREMENTS
Python 3.x
Python added to PATH during install
Non-default Python packages: numpy, chart-studio
The easiest way to install these is to use pip, Python's in-built package installer:
1. open Command Prompt (as admin)
2. type "pip install <package name>"
3. celebrate your glorious victory over the machines
"""


#%% user input

# EDIT BELOW THIS LINE ONLY
############################################################

# specify path to directory containing file, and specific file name, including ".csv" extension
# NOTE: a double backslash converts to a single backslash when specifiying paths in Windows (don't ask...), as in the example:

dirpath = "\\\\ds.strath.ac.uk\\idrive\\Science\\SIPBS\\cmac\\Tony Vassileiou\\misc scripts\\Crystalline csv induction time finder\\"
filename = "StUr_094_A Run 2.csv"

# specify parameters (instructions below)
"""
1. trans_thresh_high: the minimun transmissivity which you deem to be "clear" (e.g. 98)
2. trans_thresh_low: the maximum transmissivity which you deem to be "cloudy" (e.g. 10)
3. constant_period_A: number of time points in a row that must satisfy conditions,
   to ensure this is not a blip in the measurement
4. constant_period_B: number of time points to get to "cloudy" 
5. temp_tolerance: the allowed deviation of the actual temp. from the
   set temp. still considered "stable"
6. plot every n points in output graph (may struggle with large datasets). Note this is purely
   graphical and does not affect any calculations
7. specify number of rows (i.e. seconds if sample interval = 1/s) to ignore

If in doubt, for parameters 1-6 there are fairly sensible defaults;
parameter 7 simply refers to an initial temp. ramp that should be ignored - this is important so that the
"minimum" temperature determined ignores any initial heating
"""

trans_thresh_high = 98
trans_thresh_low = 10
constant_period_A = 5
constant_period_B = 50
temp_tolerance = 0.1
plot_every_n_points = 2
prep_rows = 1400

# DO NOT EDIT BELOW THIS LINE
############################################################


#%% import libraries

import csv
import numpy as np
import os
import chart_studio.plotly as py
import plotly.graph_objs as go
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
from datetime import datetime



#%% read file and initialise
filepath = dirpath + filename

# read in file
with open(filepath, "r") as myfile:
    file_contents = myfile.readlines()[1:] # exclude the header line

# grab relevant columns: Time, Actual T, Set T, Trans.   
nrows = len(file_contents)
Time_list = ["blank" for i in range(nrows)]
ActTemp_list = ["blank" for i in range(nrows)]
SetTemp_list = ["blank" for i in range(nrows)]
Trans_list = ["blank" for i in range(nrows)]

for i, eachline in enumerate(file_contents):
    splitline = eachline.split(",")
    Time_list[i] = splitline[0]
    ActTemp_list[i] = float(splitline[1])
    if splitline[2] == "":
        SetTemp_list[i] = 20.0
    else:
        SetTemp_list[i] = float(splitline[2])
    Trans_list[i] = float(splitline[3])

# identify max and min set temps per cycle
cycle_max_SetTemp = max(SetTemp_list[prep_rows:])
cycle_min_SetTemp = min(SetTemp_list[prep_rows:])
print(cycle_max_SetTemp)
print(cycle_min_SetTemp)

#%% main loop

flag_found_pointA = 0
flag_found_pointB = 0

j_pointA_store = []
j_pointB_store = []
j_events_store = []


for j, Time in enumerate(Time_list):
        
    # monitor progress
    #if j % 5000 == 0:
    #    print(j)

    if j <= prep_rows:
        continue

    # sanity check 1
    if flag_found_pointA == 1 and flag_found_pointB == 1:
        print("resetting A and B at: " + str(j))
        flag_found_pointA = 0
        flag_found_pointB = 0
        
       
    if flag_found_pointA == 0:
        # if you are looking for point A only
        
        if abs(ActTemp_list[j] - cycle_min_SetTemp) <= temp_tolerance and SetTemp_list[j] <= cycle_min_SetTemp:
            # if you are within defined tolerance of the min temp AND you are actually supposed to be...
            
            if not isinstance(constant_period_A, int) or constant_period_A < 1:
                # check constant_period_A is sensible...           
                print("====\nWarning: constant_period_A must be an integer value >= 1. Setting as 1 and proceeding...\n===")
                constant_period_A = 1
                
            for f in range(1,constant_period_A+1):
                try:
                    if abs(ActTemp_list[j+f] - cycle_min_SetTemp) <= temp_tolerance and SetTemp_list[j+f] <= cycle_min_SetTemp and Trans_list[j+f] >= trans_thresh_high and f == constant_period_A:
                        # if you are within defined tolerance of the min temp AND you are actually supposed to be AND transmissivity is above threshold AND this is the end of the future-check-period-thingy
                        flag_found_pointA = 1
                        print("found A at: " + str(j))
                        j_pointA_store.append(j)
                        
                    elif abs(ActTemp_list[j+f] - cycle_min_SetTemp) <= temp_tolerance and SetTemp_list[j+f] <= cycle_min_SetTemp and Trans_list[j+f] >= trans_thresh_high:
                        # if you are within defined tolerance of the min temp AND you are actually supposed to be AND transmissivity is above threshold (but still need to check more points)
                        continue
                    
                    else:
                        # if you are here, the candidate point A is invalid, and we can move on
                        break
                except IndexError:
                    # this occurs at the end of a file, where you can no longer look ahead
                    break

        else:
            # if you are here, you are looking for point A, but the temperature is not low
            if abs(ActTemp_list[j] - cycle_max_SetTemp) <= temp_tolerance:
                # this is the condition to reset and look for point A in the new cycle
                flag_found_pointA = 0
                flag_found_pointB = 0
                
    elif flag_found_pointB == 0:
        # if you are here, you have point A, and are looking for B

        if abs(ActTemp_list[j] - cycle_min_SetTemp) <= temp_tolerance and SetTemp_list[j] <= cycle_min_SetTemp and j < len(Time_list) - 1:
            # if the temperature starts climbing again, this cycle is over, and you have found nothing.
            # Special condition added: if this is the very last point, we won't accept a point B
        
            if not isinstance(constant_period_B, int) or constant_period_B < 1:
                # check constant_period_B is sensible...
                print("====\nWarning: constant_period_B must be an integer value >= 1. Setting as 10 and proceeding...\n===")
                constant_period_B = 10

            event_occurance = 0
            for g in range(1,constant_period_B+1):
                try:
                    if Trans_list[j+g] >= trans_thresh_high:
                        # if this is true, there is a later point that the solution is still clear... so let's move on to that one
                        break

                    elif Trans_list[j+g] <= trans_thresh_low:
                        # if this is true, the transmissivity has dropped sufficiently within the allowed time window for this to be deemed point B
                        flag_found_pointB = 1
                        event_occurance = 0
                        j_pointB_store.append(j)
                        print("found B at: " + str(j))
                        break

                    else:
                        event_occurance = 1
                except IndexError:
                    # this occurs at the end of a file, where you can no longer look ahead
                    break
            if event_occurance == 1:
                j_events_store.append(j)
           
        else:
            # if you are here, you are looking for point B, but the temperature is not low OR it is the final point
            if abs(ActTemp_list[j] - cycle_max_SetTemp) <= temp_tolerance or j == len(Time_list) - 1:
                # this is the condition to reset and look for point A in the new cycle
                # ending up here means you did not find point B - this needs captured
                j_pointB_store.append(None)
                print("no B found for this A")
                flag_found_pointA = 0
                flag_found_pointB = 0
                
    if abs(ActTemp_list[j] - cycle_max_SetTemp) <= temp_tolerance:
                # this is the condition to reset and look for point A in the new cycle
                flag_found_pointA = 0
                flag_found_pointB = 0
   
        
        
#%% plot stuff

ActTemp_arr = np.array(ActTemp_list)
SetTemp_arr = np.array(SetTemp_list)
Trans_arr = np.array(Trans_list)

Time0 = datetime.strptime(Time_list[0], "%m/%d/%Y %I:%M:%S %p")
Time_axis_arr = np.array([(datetime.strptime(t, "%m/%d/%Y %I:%M:%S %p") - Time0).seconds for t in Time_list])

# proof that the time step is not uniformly 1/s...
#for i,x in enumerate(Time_axis_arr):
#    try:
#        if x != Time_axis_arr[i+1]-1:
#            print("Found: " + str(x) + "   " + str(Time_axis_arr[i+1]))
#    except IndexError:
#        break

# color palette in various formats
ColourBlind10_palette_RGBstr = ['rgb(0, 107, 164)',
                                'rgb(255, 128, 14)',
                                'rgb(171, 171, 171)',
                                'rgb(89, 89, 89)',
                                'rgb(95, 158, 209)',
                                'rgb(200, 82, 0)',
                                'rgb(137, 137, 137)',
                                'rgb(162, 200, 236)',
                                'rgb(255, 188, 121)',
                                'rgb(207, 207, 207)',]

ColourBlind10_palette_RGBtup = [(0, 107, 164),
                                (255, 128, 14),
                                (171, 171, 171),
                                (89, 89, 89),
                                (95, 158, 209),
                                (200, 82, 0),
                                (137, 137, 137),
                                (162, 200, 236),
                                (255, 188, 121),
                                (207, 207, 207),]

ColourBlind10_palette_HEXstr = ['#006ba4',
                                '#ff800e',
                                '#ababab',
                                '#595959',
                                '#5f9ed1',
                                '#c85200',
                                '#898989',
                                '#a2c8ec',
                                '#ffbc79',
                                '#cfcfcf']

#ColourBlind10_palette_HEXstr = []
#for i in ColourBlind10_palette_RGBtup:
#    ColourBlind10_palette_HEXstr.append('#{:02x}{:02x}{:02x}'.format(i[0], i[1], i[2]))


# actual plot
trace0 = go.Scatter(
    x = Time_axis_arr[::plot_every_n_points],
    y = SetTemp_arr[::plot_every_n_points],
    mode = 'lines',
    name = 'Set Temperature',
    line = dict(
        color = ColourBlind10_palette_RGBstr[0]
    )
)
trace1 = go.Scatter(
    x = Time_axis_arr[::plot_every_n_points],
    y = ActTemp_arr[::plot_every_n_points],
    mode = 'lines',
    name = 'Actual Temperature',
    line = dict(
        color = ColourBlind10_palette_RGBstr[2]
    )
)
trace2 = go.Scatter(
    x = Time_axis_arr[::plot_every_n_points],
    y = Trans_arr[::plot_every_n_points],
    mode = 'lines',
    name = 'Transmissivity',
    yaxis= 'y2',
    line = dict(
        color = ColourBlind10_palette_RGBstr[1]
    )
)

data = [trace0, trace1, trace2]
IT_table = [["Cycle Number", "Time A (low T reached)", "Time B (cloud point)", "Induction Time (B - A)"]]
for i,x in enumerate(j_pointA_store):
    if j_pointB_store[i] == None:
        time_A = Time_axis_arr[x]
        data.append(
            go.Scatter(
                x = np.array([time_A, time_A]),
                y = np.array([0, ActTemp_list[x]]),
                mode = 'lines',
                name = 'Cycle #{}: no IT'.format(i+1),
                line = dict(
                    color = ColourBlind10_palette_RGBstr[3],
                    dash = 'dash'
                )
            )
        )
        IT_table.append([str(i+1), str(time_A), "None", "None"])
    else:
        time_A = Time_axis_arr[x]
        time_B = Time_axis_arr[j_pointB_store[i]]
        data.append(
            go.Scatter(
                x = np.array([time_A, time_A, None, time_B, time_B]),
                y = np.array([0, ActTemp_list[x], None, ActTemp_list[x], 0]),
                mode = 'lines',
                name = 'Cycle #{}: IT = {} s'.format(i+1, time_B-time_A),
                line = dict(
                    color = ColourBlind10_palette_RGBstr[4],
                    dash = 'dash'
                )
            )
        )
        IT_table.append([str(i+1), str(time_A), str(time_B), str(time_B-time_A)])


layout = go.Layout(
    title=filename + ' (showing every {} time points)'.format(plot_every_n_points),
    xaxis=dict(
        title='Time (s)',
        tickformat='.',
        showgrid=False
    ),
    yaxis=dict(
        title=u'Temperature (\N{DEGREE SIGN}C)',
        range=[0, 130],
        showgrid=False
    ),
    yaxis2=dict(
        title='Transmissivity',
        range=[0, 100],
        titlefont=dict(
            color='rgb(148, 103, 189)'
        ),
        tickfont=dict(
            color='rgb(148, 103, 189)'
        ),
        overlaying='y',
        side='right',
        showgrid=False
    )
)

fig = go.Figure(data=data, layout=layout)
plot(fig, filename=filepath[:-4]+'_results.html')
with open(filepath[:-4]+'_results_table.csv', 'w', newline='') as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerows(IT_table)
