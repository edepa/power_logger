#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 29 22:37:26 2024

@author: edepa
"""

import pandas as pd;
import argparse;
from datetime import datetime;
import pyinputplus as pyip;
import matplotlib.pyplot as plt;
import matplotlib.figure;
import os;
from numpy import arange;
from numpy import ndarray;
from matplotlib.axes import Axes;
import ipaddress;

class Plotter:

    want_frequency_plot: bool;
    fig: matplotlib.figure.Figure;
    axes: ndarray[Axes];
    frequency_file_list: list;

    def __init__(self,idle_power:int,ip_address:ipaddress):
        self.idle_power = idle_power;
        self.target_ip = ip_address;
        return

    def create_power_dataframe_from_csv_file(self, log_file_path:str,offset:float)->pd.DataFrame:
        # Populate the DataFrame with data structured according to ['Time','Average power (W)'],
        # where the 'Time' column contains datetime objects
        with open(log_file_path,'r') as logfile:
            source_frame = pd.read_csv(logfile,usecols=['Time','Average']);
        dataframe = pd.DataFrame(index=range(len(source_frame)),columns=['Time','Average']);
        for index,row in source_frame.iterrows(): #iterrows() returns a tuple of index and row
            this_datetime = datetime.strptime(row['Time'],'%Y-%m-%dT%H:%M:%SZ')
            dataframe.iloc[index] = [this_datetime,row['Average']+offset];
        return dataframe;
 
    def get_input_datetime(self, default_time:datetime,default_date:datetime)->datetime:
        default_time = default_time.strftime('%H:%M:%S');
        default_date = default_date.strftime('%d-%m-%Y');
        time = pyip.inputRegex(r'\d{2}:\d{2}:\d{2}', prompt="Enter the time in hh:mm:ss   format: ",blank=True);
        time = default_time if len(time)==0 else time;
        date = pyip.inputRegex(r'\d{2}-\d{2}-\d{4}', prompt="Enter the date in dd-mm-yyyy format: ",blank=True); 
        date = default_date if len(date)==0 else date;
        return (datetime.strptime(time + " " + date,'%H:%M:%S %d-%m-%Y'));

    def get_plot_range(self, period:tuple,power_data:pd.DataFrame)->tuple:
        do_not_have_good_range = True;
        while do_not_have_good_range:
            print("***LOWER LIMIT OF PLOT RANGE***");
            lower_date_time = self.get_input_datetime(period[0].time(),period[0].date());
            print("***UPPER LIMIT OF PLOT RANGE***");
            upper_date_time = self.get_input_datetime(period[1].time(),period[1].date());
            if (lower_date_time >= period[0]) and (upper_date_time <= period[1]):
                do_not_have_good_range = False;
            else:
                print("The plot range does not fall within the range of the data. Please try again\n.");
        # Check for first row which has a greater time stamp.
        condition_mask = power_data['Time'] > lower_date_time;
        lower_limit = condition_mask.idxmax()-1 if condition_mask.idxmax()>0 else 0;
        condition_mask = power_data['Time'] >= upper_date_time;
        upper_limit = condition_mask.idxmax() if power_data.iloc[condition_mask.idxmax()]['Time']<upper_date_time else condition_mask.idxmax()+1;
        return lower_limit,upper_limit;

    def transform_dataframe(self, power_data:pd.DataFrame)->pd.DataFrame:
        dataframe = pd.DataFrame(index=range(len(power_data)),columns=['Date','Time','Average power']);
        for index,row in power_data.iterrows():
            dataframe.iloc[index]['Date']           = row['Time'].date().strftime('%d-%m-%Y');
            dataframe.iloc[index]['Time']           = row['Time'].time().strftime('%H:%M:%S');
            dataframe.iloc[index]['Average power']  = row['Average'];
        return dataframe

    def create_frequency_dataframe_from_csv_file(self, log_file_path:str)->pd.DataFrame:
        # Populate the DataFrame with data structured according to ['Time','CPU0','CPU8'...'CPU7','CPU15'],
        # where the 'Time' column contains datetime objects
        with open(log_file_path,'r') as logfile:
            dataframe = pd.read_csv(logfile,sep=";");
        dataframe['Time'] = dataframe['Time'].apply(lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ'));
        return dataframe;

    def get_label(self, filename:str)->str:
        isPowerAggregateLogFile = True if "powerlog" in filename else False
        if isPowerAggregateLogFile:
            label = f"Target @IP {str(self.target_ip)} - aggregate";
        else:
            id_string = "powertop_power_blade_";
            label = "Target @IP " + filename[filename.find(id_string) + len(id_string)] + " - PowerTOP";
        return label;

    def create_axes(self,listing:str)->list:
        # Check whether a frequency file is present.
        # If so, create a 5x2 plot; otherwise create a 1x1 plot
        self.frequency_file_list = [file for file in listing if ("frequency" in file)];
        if (len(self.frequency_file_list) > 0):
            #Ask whether the user wants to plot frequency files
            want_frequency_plot_str = input("Frequency data have been found. Do you want to plot them?(Y/N)");
            if (want_frequency_plot_str=="Y" or want_frequency_plot_str=="y" or want_frequency_plot_str==""):
                self.want_frequency_plot = True;
                # Create two pairs of vertically-aligned axes - one pair for power vs time, the other for frequency vs time
                self.fig, self.axes = plt.subplots(5,2,figsize=(10,8),sharex=True);
                self.ax_power = self.axes[0];
                self.ax_freq = self.axes[1:5]
        else:
            self.want_frequency_plot = False;
            self.fig, self.axes = plt.subplots(1,1,figsize=(10,8),sharex=True);
            self.ax_power = self.axes;
        return self.ax_power;

    def artist(self,listing:str,directory:str):
        range_lower_end = datetime.max; range_upper_end = datetime.min;
        for file in listing:
            if not("frequency" in file):
                offset = self.idle_power if "powertop" in file else 0;
                label = self.get_label(file);
                power_data = self.create_power_dataframe_from_csv_file(directory+file,offset);
                period = (power_data.iloc[0]['Time'],power_data.iloc[len(power_data)-1]['Time']);    
                    
                #Declare the period for which data is available
                print("");
                print(file);
                print("Logging started on :", period[0].date(), " at ", period[0].time());
                print("Logging ended on   :", period[1].date(), " at ", period[1].time());        
                
                #Now, go and get the range of the subset of rows in power_data which the user wants to plot
                plot_range = self.get_plot_range(period,power_data);           
                #Slice the power_data along the row axis, according to plot_range
                power_data_sub_range = power_data.iloc[plot_range[0]:plot_range[1]].copy();
                range_lower_end = power_data_sub_range.iloc[0]['Time'] if power_data_sub_range.iloc[0]['Time']<range_lower_end else range_lower_end;
                l = len(power_data_sub_range) - 1;
                range_upper_end = power_data_sub_range.iloc[l]['Time'] if power_data_sub_range.iloc[l]['Time']>range_upper_end else range_upper_end;
                # Plot power use in both top sub-plots.
                if self.want_frequency_plot:
                    for ax in self.ax_power:
                        ax.plot(power_data_sub_range['Time'],power_data_sub_range['Average']);
                        ax.set_ylabel('Power (W)');
                        ax.set_title('Power use, 10 s sample period');
                        ax.grid(True);
                else:
                    self.ax_power.plot(power_data_sub_range['Time'],power_data_sub_range['Average'],label = label);
                    self.ax_power.set_ylabel('Power (W)');
                    self.ax_power.set_title('Power use, 10 s sample period');
                    self.ax_power.grid(True);
            # Now, set the range of the x-tick marks and the x-tick labels.
        xticks = [x for x in arange(range_lower_end,range_upper_end,(range_upper_end-range_lower_end)/10)];
        xtick_labels = [str(xtick.astype(datetime).time())[:8] for xtick in xticks];

                        
        if self.want_frequency_plot:
            # There should be only one frequency file; hence the [0] index.
            frequency_file = self.frequency_file_list[0]
            # frequency_data will contain one column with a datetime.datetime object, and CPUx columns (x in range(16)) with int objects
            frequency_data = self.create_frequency_dataframe_from_csv_file(directory+frequency_file);
            frequency_data_sub_range = frequency_data.iloc[plot_range[0]:plot_range[1]];
            iterator = -1;
            for col in frequency_data_sub_range.columns[1:]:
                iterator += 1;
                j = int(col[3:])%2;
                i = int(iterator/4);
                self.ax_freq[i][j].plot(frequency_data_sub_range['Time'],frequency_data_sub_range[col]);
                self.ax_freq[i][j].set_ylabel('Frequency (MHz)');
                self.ax_freq[i][j].set_title("CPU" + col + ": DVFS - selected frequency\n");
                self.ax_freq[i][j].grid(True);
            for ax in self.ax_freq[-1]:
                ax.set_xlabel('Time (hh:mm:ss)');
                ax.set_xticks(xticks);
                ax.set_xticklabels(xtick_labels);
        else:
                self.ax_power.set_xlabel('Time (hh:mm:ss)');
                self.ax_power.set_xticks(xticks);
                self.ax_power.set_xticklabels(xtick_labels);

        plt.tight_layout();
        plt.legend();
        plt.show();

        return
    