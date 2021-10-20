# Program to compute minimum angular separation between two satellites and output to 'MAS.dat'
# Author: Adam Kimbrough
# Last edited: October 25, 2021
import pandas as pd
from math import radians, cos, sin, acos, asin, sqrt, degrees
import collections
import json
from numpy import pi

dates = []
#el_list1 = []
#az_list1 = []
time_angle_dict = {}
line_list = []

# Function to find minimum angular separation from list of el and az at given timestamp
def findMinDiff(el_arr,az_arr):
    # Initialize difference as infinite
    angle = 10**3
    n = len(el_arr)
    m = len(az_arr)
    # Find the min diff by comparing difference
    # of all possible pairs in given array
    for i in range(n-1):
        for j in range(i+1,m):
            if abs(sqrt((float(el_arr[i])-float(el_arr[j]))**2 + (float(az_arr[i])-float(az_arr[j]))**2)) < float(angle):
                #diff = abs(sqrt((float(el_arr[i])-float(el_arr[j]))**2 + (float(az_arr[i])-float(az_arr[j]))**2))
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
                    continue
 

    if n == 1 or angle == 10**3:
        angle = str('180')                      
    return angle

# Create time-sorted dictionary with all az/el data at each timestamp
print('Creating time-sorted dictionary...')
with open('local_passes.dat', 'r') as infile, open('MAS.dat', 'w') as outfile:
    for line in infile:
        dates.append((line.split(' ')[3].replace(':','')))

    dates_sorted = sorted(dates)
    time_dict = pd.DataFrame(dates_sorted, columns=["x"]).groupby('x').size().to_dict()

    infile.seek(0)
    for line in infile:
        line_split = line.split(' ')
        if line_split[6] == '' and (line_split[9] == '' or line_split != ''):
            if line_split[10] == '' and line_split[11] == '':
                el = line_split[7]
                az = line_split[9]
            elif line_split[10] == '' and line_split[11] != '':
                el = line_split[7]
                if line_split[9] != '':
                    az = line_split[9]
                else:
                    az = line_split[11]
            elif line_split[10] != '':
                el = line_split[7]
                az = line_split[10]

        elif line_split[6] != '' and line_split[9] != '':
            el = line_split[6]
            az = line_split[9]
        elif line_split[6] != '' and line_split[8] != '':
            el = line_split[6]
            az = line_split[8]
        elif line_split[6] != '' and line_split[10] != '':
            el = line_split[6]
            az = line_split[10]
        
           
        if line_split[3] not in line_list:
            time_angle_dict[line_split[3]]= [[el], [az]]
            line_list.append(line_split[3])

        else:
            time_angle_dict[line_split[3]][0].append(el)
            time_angle_dict[line_split[3]][1].append(az)

## Debug code     
# reading the data from the file
#with open('time_angle_dict.dat') as f:
#    data = f.read()
      
# reconstructing the data as a dictionary
#time_angle_dict = json.loads(data)
##

# Calculate MAS from dictionary and write to file.
    print('Calculating MAS and writing to file...')
    for key in dict(sorted(time_angle_dict.items())):
        angle = findMinDiff(time_angle_dict[key][0],time_angle_dict[key][1])
        seconds = int(key[:2])*3600 + int(key[3:5])*60 + int(key[6:8])
        outfile.write(str(seconds) + '\t' + str(angle) + '\n')
        

print("Done.")
