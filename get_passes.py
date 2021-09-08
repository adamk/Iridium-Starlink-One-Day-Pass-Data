# Script to pull latest Iridium TLEs from Celestrak, run PREDICT program to compute passes
# for a given day and output to text file
# Author: Adam Kimbrough
# September 08, 2021
# HOW TO RUN: Place file inside /predict/default/ folder (with predict.qth) and run "python3 get_passes.py"
# Dependencies: skyfield API
import sys
import shutil
from datetime import datetime
import os
import math
import subprocess
from skyfield.api import load, wgs84

from itertools import islice

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
cmdln_start = 'date -d "' + date_range + ' 00:00:00 UTC" ' + '+%s'
start = os.popen(cmdln_start).read().strip()
cmdln_end = 'date -d "' + date_range + ' 23:59:59 UTC" ' + '+%s'
end = os.popen(cmdln_end).read().strip()

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
           
