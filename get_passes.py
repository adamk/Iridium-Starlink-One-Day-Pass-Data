# Script to pull latest Iridium TLEs from Celestrak, run PREDICT program to compute passes
# for a given day and output to file 'passes.dat'

# Also takes file 'new_passes.dat' (a file of Iridium NEXT passes converted to Local Time) and
# outputs the number of satellites above the horizon at each 1-second timestamp in the one-day time 
# period to file 'local_passes.dat'

# Author: Adam Kimbrough
# September 08, 2021
# HOW TO RUN: Place file inside /predict/default/ folder (with predict.qth) and run "python3 get_passes.py"
# Dependencies: skyfield API, pandas

import sys
import shutil
import os
import math
import pandas as pd
from skyfield.api import load, wgs84
from itertools import islice
from datetime import datetime

if os.path.exists('iridium.tle'):
    os.remove('iridium.tle')
stations_url = 'http://celestrak.com/NORAD/elements/iridium-NEXT.txt'
satellites = load.tle_file(stations_url, filename='iridium.tle')
print('Loaded', len(satellites), 'Iridium satellites')

by_name = {sat.name: sat for sat in satellites}
iridium_sats = list(by_name.keys())

count = 0

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
        
        
date_range = input("Enter single day as Jan 01 2021 \n")
cmdln_start = 'date -d "' + date_range + ' 04:00:00 UTC" ' + '+%s'
start = os.popen(cmdln_start).read().strip()
print(start)
date_range_end = int(date_range[4:6])+1
new_date_range = date_range.replace(date_range[4:6], str(date_range_end))
cmdln_end = 'date -d "' + str(new_date_range) + ' 03:59:59 UTC" ' + '+%s'
end = os.popen(cmdln_end).read().strip()
print(end)
time_list = []
x = 0
y = 0
while x < 18:
    time_list.append(int(start) + 5000*y)
    x+=1
    y+=1
    k = 1
sat_count = 0
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

sat_count3 = 0
with open('passes.dat', 'w') as outfile:
    while sat_count3 < len(iridium_sats):
        outfile.write(iridium_sats[sat_count3]+'\n')
        sat_count2 = 0
        sat_name = iridium_sats[sat_count3].replace(" ", "") + '.dat'
        with open(sat_name.replace(" ", "")) as infile:
            lines = infile.readlines()
            for line in lines:
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

n=0
output_file = "new_passes.dat"
new_lines = []
print('Removing duplicate timestamps...\n')
with open('passes.dat', 'r') as infile, open(output_file, 'w') as outfile:
    for line in infile:
        if n < len(iridium_sats)-1:
            if line.strip() == iridium_sats[n].strip():
                outfile.write(iridium_sats[n] + '\n')
                continue
            elif line.strip() == iridium_sats[n+1].strip():
                n += 1
                new_lines = []
                outfile.write(iridium_sats[n-1] + '\n')
                print(iridium_sats[n-1] + ' duplicates removed.')
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
    print(iridium_sats[n] + ' duplicates removed.')     

n=0

local_time = []
utc_lines = []
utc_count=0
local_day = date_range[4:6]
print('Converting UTC to Local...\n')
with open('new_passes.dat', 'r') as infile, open('local_passes.dat', 'w') as outfile:
    for line in infile:
        if n < len(iridium_sats):
            if line.strip() == iridium_sats[n].strip():
                continue
            elif line.strip() == iridium_sats[n+1].strip():     
                while utc_count < len(utc_lines):
                    utc_time = utc_lines[utc_count].split(' ')[3]
                    utc_day = utc_lines[utc_count].split(' ')[2]
                    local_line = utc_lines[utc_count].replace(utc_time[0:8],local_time[utc_count]).replace(utc_day[0:2], local_day)
                    outfile.write(local_line)
                    utc_count += 1
                utc_count = 0
                n += 1
                local_time = []
                utc_lines = []
                print(iridium_sats[n-1] + ' passes converted to local time.')                
            else:
                utc = line.split(' ')[3]
                local_hour = int(utc[0:2])-4
                if local_hour < 0:
                    local_hour = 24 + local_hour
                if local_hour > 0 and local_hour < 10:
                    local_hour = str(0) + str(local_hour)
                if local_hour == 0:
                    local_hour = str(0) + str(local_hour)
                if utc.replace(utc[0:2], str(local_hour)) not in local_time:
                    local_time.append(utc.replace(utc[0:2], str(local_hour)))
                    utc_lines.append(line)
                
        else:
            utc = line.split(' ')[3]
            local_hour = int(utc[0:2])-4
            if local_hour < 0:
                local_hour = 24 + local_hour
            if local_hour > 0 and local_hour < 10:
                local_hour = str(0) + str(local_hour)
            if local_hour == 0:
                local_hour = str(0) + str(local_hour)
            if utc.replace(utc[0:2], str(local_hour)) not in local_time:
                local_time.append(utc.replace(utc[0:2], str(local_hour)))
                utc_lines.append(line)
                
    print(iridium_sats[n] + ' times converted to local time.')
    while utc_count < len(utc_lines):
        utc_time = utc_lines[utc_count].split(' ')[3]
        utc_day = utc_lines[utc_count].split(' ')[2]
        local_line = utc_lines[utc_count].replace(utc_time[0:8],local_time[utc_count]).replace(utc_day[0:2], local_day)
        outfile.write(local_line)
        utc_count += 1
    n += 1
    print(iridium_sats[n] + ' times converted to local time.')   
    
n = 0

output_file2 = 'num_passes.dat'
dates = []

print("\nSorting times...")
with open('local_passes.dat', 'r') as infile, open(output_file2, 'w') as outfile:
    lines = infile.readlines()
    for line in lines:
        dates.append((line.split(' ')[3].replace(':','')))
    dates_sorted = sorted(dates)
    time_dict = pd.DataFrame(dates_sorted, columns=["x"]).groupby('x').size().to_dict()

    for key in time_dict:
        time = key[:2] + ':' + key[2:4] + ':' + key[4:]
        outfile.write(time +'\t'+ '# of sats above horizon: ' + str(time_dict[key]) + '\n')
    print("Number of sats at each timestamp written to file.")
 
