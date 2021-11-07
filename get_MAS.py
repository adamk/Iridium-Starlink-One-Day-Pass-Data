# Program to compute minimum angular separation between two satellites and output to 'MAS.dat'
# Author: Adam Kimbrough
# Last edited: November 07, 2021
from pyorbital.orbital import Orbital
import pandas as pd
from math import radians, cos, sin, acos, asin, sqrt, degrees
import collections
import json
from numpy import pi
import pytz
import datetime
from dateutil import tz
from skyfield.api import load, wgs84
import re

dates = []
final_el_list = []
final_az_list = []
time_angle_dict = {}
line_list = set([])

# User input for sat constellation and specific day of predictions
satellite_const = input("Enter satellite constellation \n")
start_date = input("Enter single day as %Y-%m-%d \n")
local = pytz.timezone("America/New_York")
naive = datetime.datetime.strptime(start_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
local_dt = local.localize(naive, is_dst=None)
utc_dt = local_dt.astimezone(pytz.utc)
date = utc_dt

print
ALTITUDE_ASL = 0.629
LON = -80.4235
LAT = 37.2317

iridium_sats = []
starlink_sats = []
oneweb_sats = []
gps_sats = []

## FUNCTION TO GENERATE SAT LIST
def get_gps_satellite_names():   
    # read the element file to get a list of names for the satellites
    with open('gps.txt', 'rt') as f:
        for l in f:
            if not re.match('^[12] ', l):
                name = l.strip()
                gps_sats.append(name)
    print('Loaded', len(gps_sats), 'GPS satellites')

## FUNCTION TO GENERATE SAT LIST
def get_oneweb_satellite_names():   
    # read the element file to get a list of names for the satellites
    with open('oneweb.txt', 'rt') as f:
        for l in f:
            if not re.match('^[12] ', l):
                name = l.strip()
                oneweb_sats.append(name)
    print('Loaded', len(oneweb_sats), 'OneWeb satellites')

## FUNCTION TO REMOVE DUMMY MASS SATS AND GENERATE SAT LIST
def get_iridium_satellite_names():
    
    # read the element file to get a list of names for the satellites
    with open('iridium.txt', 'rt') as f:
        for l in f:
            if not re.match('^[12] ', l) and not l.startswith('DUMMY MASS'):
                name = l.strip()
                iridium_sats.append(name)
    print('Loaded', len(iridium_sats), 'Iridium-NEXT satellites')

## FUNCTION TO REMOVE LOW PERIGEE SATS + OTHERS AND GENERATE SAT LIST
def get_starlink_satellite_names():
    print('Removing satellites below 400km perigee...')
    remove_sats = []
    from skyfield.api import Topos, EarthSatellite, load
    ts = load.timescale()
    lines = []
    from itertools import islice
    with open('starlink.txt') as f :
        while True:
            next_n_lines = list(islice(f, 3))
            if not next_n_lines:
                break
            lines.append(next_n_lines)

    for line in lines:
        satellite = EarthSatellite(line[1], line[2], line[0], ts)
        #print(line)
        t = ts.utc(2021, 10, 12, range(0,1440))
        geocentric = satellite.at(t)
        #print(f"max {max(geocentric.distance().km)-6378}")
        if min(geocentric.distance().km)-6378 <= 400:
            #print(line)
            low_sat = line[0].split(' ')[0]
            print('Removed ' + low_sat)
            remove_sats.append(low_sat)
        #print(f"min {min(geocentric.distance().km)-6378}")
    # read the element file to get a list of names for the satellites
    with open('starlink.txt', 'rt') as f:
        for l in f:
            if not re.match('^[12] ', l) and not l.find('DARKSAT') != -1 and not l.startswith('FALCON') and not l.startswith('TYVAK') and not l.startswith('CAPELLA') and (any([l.startswith(x) for x in remove_sats])) != True:
                name = l.strip()
                #print(name)
                starlink_sats.append(name)
    print('Loaded', len(starlink_sats), 'Starlink satellites')
   
# Function to find minimum angular separation from list of el and az at given timestamp
def findMinDiff(el_arr,az_arr):
    # Initialize difference as infinite
    diff = 10**3
    n = len(el_arr)
    m = len(az_arr)
    # Find the min diff by comparing difference
    # of all possible pairs in given array
    for i in range(n-1):
        for j in range(i+1,m):
            min_el1 = float(el_arr[i])
            min_el2 = float(el_arr[j])
            min_az1 = float(az_arr[i])
            min_az2 = float(az_arr[j])
            az_diff = abs(min_az1 - min_az2)
            if az_diff > 180:
                az_diff = 360 - az_diff
            cos_az = cos(az_diff*(pi/180))
            coalt1 = 90 - min_el1
            coalt2 = 90 - min_el2
            cos_el1 = cos(coalt1 * (pi/180))
            cos_el2 = cos(coalt2 * (pi/180))
            sin_el1 = sin(coalt1 * (pi/180))
            sin_el2 = sin(coalt2 * (pi/180))
            rhs = cos_el1*cos_el2 + sin_el1*sin_el2*cos_az
            if rhs <= 1.0:
                angle = degrees(acos(rhs))
            else:
                print('Could not calculate minimum angle of separation')
            if float(angle) < diff:
                #diff = abs(sqrt((float(el_arr[i])-float(el_arr[j]))**2 + (float(az_arr[i])-float(az_arr[j]))**2))
                diff = angle

    if n == 1 or angle == 10**3:
        diff = str('180')                      
    return diff

## FUNCTION TO PARSE TLE FOR PASSES
def do_calc(d, sat_name, satellite_const):
    if satellite_const.lower() == 'iridium':
        orb = Orbital(sat_name, 'iridium.txt')
    if satellite_const.lower() == 'starlink':
        orb = Orbital(sat_name, 'starlink.txt')
    if satellite_const.lower() == 'oneweb':
        orb = Orbital(sat_name, 'oneweb.txt')
    if satellite_const.lower() == 'gps':
        orb = Orbital(sat_name, 'gps.txt')
    passes = orb.get_next_passes(d, 24, LON, LAT, ALTITUDE_ASL, horizon=1)
    #print(passes)
    #rise_az, rise_el = orb.get_observer_look(passes[0][0], LON, LAT, ALTITUDE_ASL)
    #transit_az, transit_el = orb.get_observer_look(passes[0][2], LON, LAT, ALTITUDE_ASL)
    #set_az, set_el = orb.get_observer_look(passes[0][1], LON, LAT, ALTITUDE_ASL)
    print(sat_name)
    #print(passes[0][0], rise_az, rise_el)
    #print(passes[0][1], set_az, set_el)
    #rise_time = passes[0][0].strftime("%H:%M:%S")
    #fall_time = passes[0][1].strftime("%H:%M:%S")

    n = 0
    count = 0
    for sat_pass in passes:
        start_time = passes[n][0]
        stop_time = passes[n][1]
        current_time = start_time
        while current_time <= stop_time:
            #pass_vel = orb.get_position(start_time.date(),normalize=False)[1]
            #pass_vel_mag = sqrt((pass_vel[0]**2)+(pass_vel[1]**2)+(pass_vel[2]**2))
            az, el = orb.get_observer_look(current_time, LON, LAT, ALTITUDE_ASL)
            dates.append(current_time.astimezone(local).strftime("%H:%M:%S"))
            final_az_list.append(az)
            final_el_list.append(el)
            #print(current_time.date())
            #print(current_time.strftime("%H:%M:%S"))
            #print(az)
            #print(el)
            current_time += datetime.timedelta(seconds=1)         
        n+=1


if satellite_const.lower() == 'iridium':
    stations_url = 'https://celestrak.com/NORAD/elements/iridium-next.txt'
    satellites = load.tle_file(stations_url, filename='iridium.txt')
    get_iridium_satellite_names() 
    for sat in iridium_sats:
        #final_az_list.append(sat)
        #final_el_list.append(sat)
        do_calc(date, sat, satellite_const)

if satellite_const.lower() == 'starlink':
    stations_url = 'https://celestrak.com/NORAD/elements/starlink.txt'
    satellites = load.tle_file(stations_url, filename='starlink.txt')
    get_starlink_satellite_names() 
    for sat in starlink_sats:
        #final_az_list.append(sat)
        #final_el_list.append(sat)
        do_calc(date, sat, satellite_const)

if satellite_const.lower() == 'oneweb':
    stations_url = 'https://celestrak.com/NORAD/elements/oneweb.txt'
    satellites = load.tle_file(stations_url, filename='oneweb.txt')
    get_oneweb_satellite_names()
    for sat in oneweb_sats:
        #final_az_list.append(sat)
        #final_el_list.append(sat)
        do_calc(date, sat, satellite_const)

if satellite_const.lower() == 'gps':
    stations_url = 'https://celestrak.com/NORAD/elements/gps-ops.txt'
    satellites = load.tle_file(stations_url, filename='gps.txt')
    get_gps_satellite_names()
    for sat in gps_sats:
        #final_az_list.append(sat)
        #final_el_list.append(sat)
        do_calc(date, sat, satellite_const)


with open("local_passes_" +satellite_const.lower() + ".dat","w") as f:
    for i in range(0, len(dates)):
        f.write("{0}\t{1}\t{2}\n".format(dates[i],final_el_list[i], final_az_list[i]))


# Create time-sorted dictionary with all az/el data at each timestamp
print('Creating time-sorted dictionary...')
with open('local_passes_' +satellite_const.lower()+'.dat', 'r') as infile, open('MAS_' + satellite_const.lower()+'.dat', 'w') as outfile:
    n=0
    for line in infile:
        if dates[n] not in line_list:
            time_angle_dict[dates[n]] = [[final_el_list[n]], [final_az_list[n]]]
            line_list.add(dates[n])
        else:
            time_angle_dict[dates[n]][0].append(final_el_list[n])
            time_angle_dict[dates[n]][1].append(final_az_list[n])
        n+=1

    with open('time_angle_dict.txt', 'w') as convert_file:
        convert_file.write(json.dumps(time_angle_dict))
     
# Calculate MAS from dictionary and write to file.
    print('Calculating MAS and writing to file...')
    for key in dict(sorted(time_angle_dict.items())):
        angle = findMinDiff(time_angle_dict[key][0],time_angle_dict[key][1])
        seconds = int(key[:2])*3600 + int(key[3:5])*60 + int(key[6:8])
        outfile.write(str(seconds) + '\t' + str(angle) + '\n')
print("Done.")
