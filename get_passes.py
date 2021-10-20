# Script to pull latest Iridium TLEs from Celestrak, run PREDICT program to compute passes
# for a given day and output to file 'passes.dat' and 'local_passes.dat'

# Also takes file 'new_passes.dat' (a file of Iridium NEXT passes converted to Local Time) and
# outputs the number of satellites above the horizon at each 1-second timestamp in the one-day time 
# period to file 'num_passes.dat'

# Author: Adam Kimbrough
# September 21, 2021
# HOW TO RUN: Place file inside /predict/default/ folder (with predict.qth) and run "python3 get_passes.py"
# Dependencies: skyfield API, pandas

import sys
import shutil
import os
import math
import re
import pandas as pd
from skyfield.api import load, wgs84
from itertools import islice
from datetime import datetime

# Pull latest Iridium-NEXT TLE Data
if os.path.exists('iridium.tle'):
    os.remove('iridium.tle')
stations_url = 'http://celestrak.com/NORAD/elements/iridium-NEXT.txt'
satellites = load.tle_file(stations_url, filename='iridium.tle')

print('Loaded', len(satellites), 'Iridium satellites')

by_name = {sat.name: sat for sat in satellites}
iridium_sats = list(by_name.keys())

count = 0

# Separate TLE data into multiple files for PREDICT to process w/o error (maximum TLE line limit)
with open('iridium.tle', 'r') as infile:
    with open('iridium1.tle', 'w') as outfile:
        for TLE in list(islice(infile, 72)):
            outfile.write(TLE)
    with open('iridium2.tle', 'w') as outfile:
        for TLE in list(islice(infile, 72)):
            outfile.write(TLE)
    with open('iridium3.tle', 'w') as outfile:
        for TLE in list(islice(infile, 72)):
            outfile.write(TLE)
    with open('iridium4.tle', 'w') as outfile:
        for TLE in list(islice(infile, 72)):
            outfile.write(TLE)         
        
# User input for specific day of predictions       
date_range = input("Enter single day as Jan 01 2021 \n")
cmdln_start = 'date -d "' + date_range + ' 04:00:00 UTC" ' + '+%s'
start = os.popen(cmdln_start).read().strip()
print(start)
date_range_end = int(date_range[4:6])+1
new_date_range = re.sub("(\w{3} )\d{2}( \d{4})", r"\g<1>%02d\g<2>" % date_range_end, date_range)
print(new_date_range)
cmdln_end = 'date -d "' + str(new_date_range) + ' 03:59:59 UTC" ' + '+%s'
end = os.popen(cmdln_end).read().strip()
print(end)
k = 1
sat_count = 0
# Run PREDICT on all Iridium-NEXT satellites given the date input
while k <= 3:
    count = 0
    while count < 24:
        cmdln_predict = 'predict -q predict.qth -t iridium' + \
            str(k) + '.tle -f "' + iridium_sats[sat_count] + '" ' + start + ' ' + end + \
            ' -o ' + iridium_sats[sat_count].replace(" ", "") + '.dat'
        print(cmdln_predict)
        os.system(cmdln_predict)
        sat_count += 1
        count += 1
    k += 1
count4 = 1
while count4 <= 3:
    cmdln_predict = 'predict -q predict.qth -t iridium4.tle -f "' + iridium_sats[sat_count] + '" '+ \
    start + ' ' + end + ' -o ' + iridium_sats[sat_count].replace(" ", "") + '.dat'
    print(cmdln_predict)
    os.system(cmdln_predict)
    count4 += 1
    sat_count += 1
# Write pass data into 'passes.dat'
sat_count3 = 0
with open('passes.dat', 'w') as outfile:
    while sat_count3 < len(iridium_sats):
        outfile.write(iridium_sats[sat_count3]+'\n')
        sat_count2 = 0
        sat_name = iridium_sats[sat_count3].replace(" ", "") + '.dat'
        with open(sat_name.replace(" ", "")) as infile:
            for line in infile:
                if line.split(' ')[4] == '':
                    if line.split(' ')[5] == '':
                        if line.split(' ')[6] == '':
                            if int(line.split(' ')[7]) > 0:
                                outfile.write(line)
                        elif int(line.split(' ')[6]) > 0:
                            outfile.write(line)
                    elif int(line.split(' ')[5]) > 0:
                        outfile.write(line)
        print(sat_name + " passes merged")
        os.remove(sat_name)
        sat_count3 += 1

# Remove the duplicate timestamps
n=0
output_file = "new_passes.dat"
new_lines = []
first = 0
print('Removing duplicate timestamps...\n')
with open('passes.dat', 'r') as infile, open(output_file, 'w') as outfile:
    for line in infile:
        if n < len(iridium_sats):
            if line.strip() == iridium_sats[n].strip():
                if first == 1:
                    print(iridium_sats[n-1] + ' duplicates removed.')
                outfile.write(iridium_sats[n] + '\n')
                n += 1
                new_lines = []
                first = 1
                continue
                
            else:
                time = line.split(' ')[3]
                if time not in new_lines:
                    outfile.write(line)
                    new_lines.append(time)    
    else:
        time = line.split(' ')[3]
        if time not in new_lines:
           outfile.write(line)
           new_lines.append(time)    
    print(iridium_sats[n-1] + ' duplicates removed.')

# Convert the UTC time to Local (ET) and write to 'local_passes.dat'
n=0
local_day = date_range[4:6]
print('Converting UTC to Local...\n')
with open('new_passes.dat', 'r') as infile, open('local_passes.dat', 'w') as outfile:
    for line in infile:
        if n < len(iridium_sats):
            if line.strip() == iridium_sats[n].strip():
                n += 1       
                continue
            else:
                utc = line.split(' ')[3]
                local_hour = int(utc[0:2])-4
                if local_hour < 0:
                    local_hour = 24 + local_hour
                elif local_hour > 0 and local_hour < 10:
                    local_hour = str(0) + str(local_hour)
                elif local_hour == 0:
                    local_hour = str(0) + str(local_hour)
                else:
                    local_hour = int(utc[0:2])-4
                new_line = re.sub("\d{2}(\:\d{2}:\d{2})", r"%02d\1" % int(local_hour), line)
                local_line = re.sub("\d+(?=[A-Z])", local_day, new_line)
                outfile.write(local_line) 
    print('Done.')
      
    
n = 0
output_file2 = 'num_passes.dat'
dates = []

# Sort the times from 00:00:00 to 23:59:59 and write the # of passes at each timestamp to 'num_passes.dat'
print("\nSorting times...")
with open('local_passes.dat', 'r') as infile, open(output_file2, 'w') as outfile:
    for line in infile:
        dates.append((line.split(' ')[3].replace(':','')))
    dates_sorted = sorted(dates)
    time_dict = pd.DataFrame(dates_sorted, columns=["x"]).groupby('x').size().to_dict()


    for key in time_dict:
        time = key[:2] + ':' + key[2:4] + ':' + key[4:]
        outfile.write(time +'\t'+ '# of sats above horizon: ' + str(time_dict[key]) + '\n')
    print("Number of sats at each timestamp written to file.")
