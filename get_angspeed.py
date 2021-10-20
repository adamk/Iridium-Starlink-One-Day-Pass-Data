# Computes apparent angular speed of Iridium-Next or Starlink satellites
# Author: Adam Kimbrough
# Last Edited: October 20, 2021

from pyorbital.orbital import Orbital
from math import sin,cos,acos,asin,sqrt,pi
import datetime
from skyfield.api import load, wgs84
import os
import re
import pytz

output_file = "new_azel.dat"
final_az_list = []
final_el_list = []

# User input for sat constellation and specific day of predictions
satellite_const = input("Enter satellite constellation \n")
start_date = input("Enter single day as %Y-%m-%d \n")
local = pytz.timezone("America/New_York")
naive = datetime.datetime.strptime(start_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
local_dt = local.localize(naive, is_dst=None)
utc_dt = local_dt.astimezone(pytz.utc)
date = datetime.datetime(int(start_date[0:4]), int(start_date[5:7]),int(start_date[8:10]), 0, 0, 0)
print
ALTITUDE_ASL = 0.629
LON = -80.4235
LAT = 37.2317

iridium_sats = []
starlink_sats = []

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
    
## FUNCTION TO CALCULATE APPARENT ANGLE
def findMinDiff(el1,az1,el2,az2):
    # Initialize difference as infinite
    diff = 10**3
    n = 2
    m = 2
    # Find the min diff by comparing difference of all possible pairs in given array
    for i in range(n-1):
        for j in range(i+1,m):
            if abs(sqrt((float(el1)-float(el2))**2 + (float(az1)-float(az2))**2)) < diff:
                #diff = abs(sqrt((float(el1)-float(el2))**2 + (float(az1)-float(az2))**2))
                min_el1 = float(el1)
                min_el2 = float(el2)
                min_az1 = float(az1)
                min_az2 = float(az2)
    
    if n == 1:
        angle = str('180')
    else:                       
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
        if rhs < 1.0:
            angle = acos(rhs)*(180/pi)
        else:
            angle = str('180')

    # Return min diff
    if diff == 10**3:
        diff = str('180')
    return angle
    
## FUNCTION TO PARSE TLE FOR PASSES
def do_calc(d, sat_name, satellite_const):
    if satellite_const.lower() == 'iridium':
        orb = Orbital(sat_name, 'iridium.txt')
    if satellite_const.lower() == 'starlink':
        orb = Orbital(sat_name, 'starlink.txt')
    passes = orb.get_next_passes(d, 24, LON, LAT, ALTITUDE_ASL, horizon=30)
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
            final_az_list.append(az)
            final_el_list.append(el)
            #print(current_time.date())
            #print(current_time.strftime("%H:%M:%S"))
            #print(az)
            #print(el)
            current_time += datetime.timedelta(seconds=1)
        n+=1
        count+=1
        if count < len(passes):
            final_az_list.append('NEW PASS')
            final_el_list.append('NEW PASS')
   
if satellite_const.lower() == 'iridium':
    stations_url = 'https://celestrak.com/NORAD/elements/iridium-next.txt'
    satellites = load.tle_file(stations_url, filename='iridium.txt')
    get_iridium_satellite_names() 
    for sat in iridium_sats:
        final_az_list.append(sat)
        final_el_list.append(sat)
        do_calc(date, sat, satellite_const)

if satellite_const.lower() == 'starlink':
    stations_url = 'https://celestrak.com/NORAD/elements/starlink.txt'
    satellites = load.tle_file(stations_url, filename='starlink.txt')
    get_starlink_satellite_names() 
    for sat in starlink_sats:
        final_az_list.append(sat)
        final_el_list.append(sat)
        do_calc(date, sat, satellite_const)
        
print("Writing to 'new_azel.dat'...")
out = "\n".join("{} {}".format(x, y) for x, y in zip(final_el_list, final_az_list))
with open(output_file, "w") as file:
    file.write(out)
print("Done.")
    

print("Calculating angular speeds and writing to ang_speed.dat...")
n = 0
getStarted2 = False
getStarted = True
with open('new_azel.dat', 'r') as infile, open('ang_speed.dat', 'w') as outfile:
    next(infile)
    for line in infile:
        if n == 0:
            old_el = line.split(' ')[0]
            old_az = line.split(' ')[1]
            n = 1

        elif line.split(' ')[0].startswith('NEW') or line.split(' ')[0].startswith('IRIDIUM') or line.split(' ')[0].startswith('STARLINK'):
            getStarted = True
            getStarted2 = False
            n = 0
            continue
            
        elif n == 1:
            el = line.split(' ')[0]
            az = line.split(' ')[1]
            ang_speed = findMinDiff(el, az, old_el, old_az)
            outfile.write(str(ang_speed)+'\n')
            old_el = el
            old_az = az
            n = 2

        else:
            el = line.split(' ')[0]
            az = line.split(' ')[1]
            ang_speed = findMinDiff(el, az, old_el, old_az)
            outfile.write(str(ang_speed)+'\n')
            old_el = el
            old_az = az
            n = 1


