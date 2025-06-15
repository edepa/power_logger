#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import asyncio
import ipaddress
from logger import PowerLogger, TimeoutException
from plotter import Plotter
import os

def valid_ip(s)->ipaddress.IPv4Address:
    try:
        return ipaddress.ip_address(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid IP address: {s}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Logs power usage to file via RedFish API.")
    parser.add_argument('ip_address', type=valid_ip, help="IP address to connect to")
    parser.add_argument('want_immediate_reading', type=str, choices=["True", "False"],
                        help="Immediate reading before scheduling? (True/False)")
    parser.add_argument('timeout_duration', type=int,
                        help="Duration to keep logging (in seconds)")
    parser.add_argument('idle_power',type=float, nargs='?', default=0, help="Idle power to add to powertop's dynamic power measurement");
    args = parser.parse_args();

    # Instantiate logger
    logger = PowerLogger(args.ip_address)
    # Instantiate plotter
    plotter = Plotter(args.idle_power,args.ip_address);

    # Immediate reading if requested
    if args.want_immediate_reading == "True":
        print("Gathering data from target immediately...")
        logger.write_to_file(logger.read_target());    

    # Run the logging loop with timeout
    try:
        asyncio.run(logger.run(args.timeout_duration))
    except (TimeoutException, KeyboardInterrupt):
        print("Gathering data since last data collection and now ...")
        logger.write_to_file(logger.read_target());    
        logger.copy_log_to_plot()

    # Run the plotter on the logged data.
    directory = logger.get_plot_directory();
    listing = os.listdir(directory);
    plotter.create_axes(listing);                   # plotter reads the listing to identify the presence of various types of log file
    plotter.artist(listing,f"{directory}/");
