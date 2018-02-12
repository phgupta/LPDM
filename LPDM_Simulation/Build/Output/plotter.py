########################################################################################################################
# *** Copyright Notice ***
#
# "Price Based Local Power Distribution Management System (Local Power Distribution Manager) v2.0"
# Copyright (c) 2017, The Regents of the University of California, through Lawrence Berkeley National Laboratory
# (subject to receipt of any required approvals from the U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this software, please contact
# Berkeley Lab's Innovation & Partnerships Office at  IPO@lbl.gov.
########################################################################################################################


"""Scripts for plotting power outputs"""

import json
import logging
import os
import re
import shutil
import csv
import sys
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import PyQt5
import seaborn as sb

LOGSDIR = 'logs' # location of logs relative to base directory
FIRSTLINE = 3 # first line index of log
PLOTSDIR = 'Plots' # location of plots relative to base directory

##################################################################
# Directory stuff
##################################################################

##
# Searches through all of the existing log folder names and finds the unique simulation ID
# of the most recent log created 
def get_last_log():
    base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname( \
        os.path.realpath(__file__)))), "logs")
    max_id = 0
    for dirname in os.listdir(base_path):
        if re.match(r'^simulation_(\d+)$', dirname):
            parts = dirname.split("_")
            current_id = int(parts[1])
            if current_id > max_id:
                max_id = current_id
    return 'simulation_' + str(max_id)

##
# Deletes all items in the logs and plots folders 
def clean_workspace():
    folder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname( \
        os.path.realpath(__file__)))), "logs")
    clean_folder(folder_path)
    folder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname( \
        os.path.realpath(__file__)))), "Plots")
    clean_folder(folder_path)

def clean_folder(folder_path):
    for file_object in os.listdir(folder_path):
        file_object_path = os.path.join(folder_path, file_object)
        if os.path.isfile(file_object_path):
            os.unlink(file_object_path)
        else:
            shutil.rmtree(file_object_path)

##################################################################
# CSV stuff
##################################################################

def create_CSVs(sim_folder):
    log_path = os.path.join('logs', sim_folder, 'sim_results.log')
    csv_directory = os.path.join(PLOTSDIR, sim_folder)
    if not os.path.isdir(csv_directory):
        os.makedirs(csv_directory)
    with open(log_path) as file:
        lines = file.readlines()
    # get list of devices
    devices = []
    for ind in range(FIRSTLINE, len(lines)):
        line = lines[ind]
        device = parse_initialize(line)
        if device != None:
            devices.extend([device])
        else:
            break
    # sort log lines to be just power, and not grid controller
    lines = [line for line in lines if is_power_message(line)]
    lines = [line for line in lines if not is_gc(line)]
    # read all lines, parse power
    device_data = {}
    for line in lines:
        device, time, power = parse_power(line)
        if device not in device_data:
            device_data[device] = [[time, power]]
        else:
            device_data[device].append([time, power])
    # delete small time deviations
    for device in device_data.keys():
        dataArr = device_data[device]
        i = 0
        while i < len(dataArr)-2:
            if float(dataArr[i+1][0]) - float(dataArr[i][0]) < 10:
                dataArr.pop(i)
            else:
                i = i + 1
    # create output directory and write CSVs
    for device in device_data:
        write_CSV(os.path.join(csv_directory, device + '.csv'), device_data[device])

def parse_initialize(line):
    split = line.split('; ')
    if split[5][:10] == 'initialize':
        return split[2]
    else:
        return None
    
def is_power_message(line):
    split = line.split('; ')
    if len(split) < 4:
        return False
    return split[3][:9] == 'power_msg'

def is_gc(line):
    split = line.split('; ')
    if len(split) < 3:
        return False
    return split[2][:2] == 'gc'

def parse_power(line): # device, time, power
    split = line.split('; ')
    if len(split) < 6:
        return None, None
    else:
        return split[2], split[1], split[4]

def write_CSV(filePath, data):
    csvFile, writer = open_CSV(filePath)
    writer.writerows(data)
    csvFile.close()
    
def open_CSV(filePath):
    if sys.version_info[0] == 2:  # Not named on 2.6
        access = 'wb'
        kwargs = {}
    else:
        access = 'wt'
        kwargs = {'newline':''}    
    csvfile = open(filePath, access, **kwargs)
    csvfile.truncate()
    writer = csv.writer(csvfile)
    return csvfile, writer

##################################################################
# Plot stuff
##################################################################

def create_plots(sim_folder):
    csv_directory = os.path.join(PLOTSDIR, sim_folder)
    for file_name in os.listdir(csv_directory):
        if file_name.endswith(".csv"):
            csv_path = os.path.join(csv_directory, file_name)
            power_data = read_csv(csv_path)
            power_plot(power_data, csv_directory, file_name.split('.')[0])

def read_csv(csv_path):
    file_handle = open(csv_path, 'rU')
    reader = csv.reader(file_handle)
    datalist = list(reader)
    datalist = datalist[1:] # get rid of header
    data = np.array(datalist)
    data = data.astype('float')
    file_handle.close()
    return data

def power_plot(data, output_directory, output_name):
    TIMESCALE = 3600 # seconds in an hour
    time, power = modifyToZOH(data[:,0], data[:,1])
    duration = time[-1]
    tick_inc = 24
    sb.set_style("darkgrid")
    fig = plt.figure()
    matplotlib.rcParams.update({'font.size': 8})
    #plt.switch_backend('Qt5Agg')
    figManager = plt.get_current_fig_manager()
    #figManager.window.showMaximized()
    ax = tranPlot(fig, 111, 'Power (W)', 0, duration, TIMESCALE, tick_inc)
    ax.plot(time/TIMESCALE, power, 'red', label=output_name)
    ax.legend(loc='upper right')
    # Save figure to file
    plt.savefig(os.path.join(output_directory, output_name + '.pdf'), \
        bbox_inches='tight')
    plt.close(fig)

def modifyToZOH(time, data):
    # insert entries for zero order hold interpolation
    arr = np.array([time, data]).T
    r = 1
    while r < len(arr[:,0]):
        newRow = np.array([arr[r,0], arr[r-1, 1]])
        arr = np.insert(arr, r, newRow, axis=0)
        r = r + 2
    return arr[:,0], arr[:,1]

def tranPlot(fig, subplot, ylabel, startTime, duration, timeScale, tickInc):
    ax = fig.add_subplot(subplot)
    ax.grid(True, linestyle='dotted')
    ax.set_xlim([startTime/timeScale, (startTime + duration)/timeScale])
    ax.set_xticks(range(int(startTime/timeScale), \
        int((startTime + duration)/timeScale + 1), tickInc))
    ax.set_ylabel(ylabel)
    return ax    