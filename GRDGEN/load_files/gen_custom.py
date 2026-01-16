#!/usr/bin/env python

# *********************************************************************
# PROGRAM TO GENERATE A CUSTOM LOAD GRID
# :: GRIDS GENERATED MAY BE USED BY LOADDEF (run_cn.py) OR IN GMT
# 
# Copyright (c) 2014-2019: HILARY R. MARTENS, LUIS RIVERA, MARK SIMONS         
#
# This file is part of LoadDef.
#
#    LoadDef is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    any later version.
#
#    LoadDef is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with LoadDef.  If not, see <https://www.gnu.org/licenses/>.
#
# *********************************************************************

# %%
# MODIFY PYTHON PATH TO INCLUDE 'LoadDef' DIRECTORY
from __future__ import print_function
import sys
import os
sys.path.append(os.getcwd() + "/../../")

# IMPORT PYTHON MODULES
import numpy as np
import pandas as pd
import scipy as sc
import netCDF4
from CONVGF.utility import read_AmpPha

# %% CH: I am editing the code to run it trhought several squares each with fixed coordinates. 
# I want to  keep the coordinates to calculate the deformation of each square at different points over the study area 
# All the results will be added for each subarea
# March 28, 2024 (Seasonal project)
# Adding information for Amite River (01/13/2025)
# MR folder C:\Users\carol\Box Sync\Shapefiles_06Seasonal\MR_load\MR_load_loaddef.csv
# AM folder C:\Users\carol\Box\Tulane\Shapefiles_06Seasonal\AR_load\AR_load_loadef.csv
df = pd.read_csv(r"C:\Users\carol\Box\Tulane\Shapefiles_06Seasonal\AR_load\AR_load_loadef.csv")
squares = df[df["type"]=="square"]
squares = squares.drop(columns=["type"])
squares["id"] = squares["id"].astype(int)
squares.set_index("id", inplace=True)
squares.sort_index(inplace=True)

# CH: The original script creates a grid between -90 to 91 in lat and 0 to 360 in lon. Creating that grid takes a lot of time and I don't need that. Then use the variables to change the extent of the load grid
ext_n= 31.
ext_s = 30.
ext_e = 269.5
ext_w = 268.
# Heighs MR
# heights =[8.41, 8.47, 10.71, 10.87, 10.56, 9.4, 6.93, 5.05, 4.31, 4.28, 4.93, 5.26]
# Heighs AR  [4.63, 4.84, 4.23, 4.78, 4.44, 3.79, 3.89, 4.01, 3.56, 3.44, 3.36, 3.98], just use the month with more and less water (feb and nov)
heights =[4.84, 3.36]

# %%
for h in heights:
    number = 0
    for index in squares.index:

        # --------------- SPECIFY USER INPUTS --------------------- #
        # Specify Bounding Box for Load Model (e.g. boundingbox.klokantech.com)
        #  :: In general, the longitude range should be [0,360]
        #  :: In the special case that the bounding box crosses the prime meridian,
        #     the range should be [-180,0] for wlon and [0,180] for elon

        # CH: I am changing the original code to calculate the longitudes to 360 + longitude because all my 
        # longitudes are negative but the special case does not apply because both sides of the bounding 
        # box are crossing the prime meridian

        wlon= 360. + squares["west"][index] # range [0,360] | If Bounding Box Crosses Prime Meridian, range = [-180,0]
        elon= 360. + squares["east"][index] # range [0,360] | If Bounding Box Crosses Prime Meridian, range = [0,180]
        slat= squares["south"][index]  # range [-90,90]
        nlat= squares["north"][index]  # range [-90,90]

        # Apply Prime-Meridian Correction?
        #  :: Set to "True" if the Bounding Box Stradles the Prime Meridian
        #  :: Ranges Must be [-180,0] and [0,180]
        pm_correct = False

        # Specify Load Height (meters)
        loadamp=h

        # Specify Phase (deg)
        loadpha=0.0

        # Apply the Given Load Height and Phase to the Region Outside the Bounding Box
        set_outside = False

        # Apply the Given Load Height and Phase to the Region Inside the Bounding Box
        set_inside = True

        # Optional: Starting Grid File (If no initial starting grid, set "initial_grid = None")
        initial_grid = None
        regular_grid = True

        # Grid Spacing
        #  :: Only used if a starting grid file is not supplied
        gspace = 0.0005

        # Output Filename
        number = number +1
        outfile = ("AR_load_BRregion_"+str(loadamp)+"m-area"+str(number))

        # Write Load Information to a netCDF-formatted File? (Default for convolution)
        write_nc = True

        # Write Load Information to a Text File? (Alternative for convolution)
        write_txt = True

        # Write Load Information to a GMT-formatted File? (Lon, Lat, Amplitude)
        write_gmt = False

        # ------------------ END USER INPUTS ----------------------- #


        # -------------------- BEGIN CODE -------------------------- #

        # Check for output of a file
        if (write_nc == False) and (write_txt == False) and (write_gmt == False):
            print(":: Error: No output file(s) selected. Options: netCDF, GMT, and/or plain-text.")
            sys.exit()

        # Create Folders
        if not (os.path.isdir("../../output/Grid_Files/")):
            os.makedirs("../../output/Grid_Files/")
        if not (os.path.isdir("../../output/Grid_Files/GMT/")):
            os.makedirs("../../output/Grid_Files/GMT/")
        if not (os.path.isdir("../../output/Grid_Files/GMT/Custom/")):
            os.makedirs("../../output/Grid_Files/GMT/Custom/")

        if not (os.path.isdir("D:/06Seasonal/LoadDef_Amite/output/Grid_Files/nc/")): #D:/06Seasonal/LoadDef_Amite/output/Grid_Files/nc/Custom
            os.makedirs("D:/06Seasonal/LoadDef_Amite/output/Grid_Files/nc/")
        if not (os.path.isdir("D:/06Seasonal/LoadDef_Amite/output/Grid_Files/nc/Custom/")):
            os.makedirs("D:/06Seasonal/LoadDef_Amite/output/Grid_Files/nc/Custom/")

        if not (os.path.isdir("../../output/Grid_Files/text/")):
            os.makedirs("../../output/Grid_Files/text/")
        if not (os.path.isdir("../../output/Grid_Files/text/Custom/")):
            os.makedirs("../../output/Grid_Files/text/Custom/")

        # Read in Starting Grid, or Generate a New Grid
        if initial_grid is not None:
            # Read in Starting Grid
            llat,llon,amp,pha,lat1dseq,lon1dseq,amp2darr,pha2darr = read_AmpPha.main(initial_grid,regular_grid=regular_grid)
        # Generate New Grid
        else:
            lats = np.arange(30.,31.,gspace) + (gspace/2.0)
            lons = np.arange(268.,269.,gspace) + (gspace/2.0)
            xv,yv = np.meshgrid(lons,lats)
            llon = np.ravel(xv)
            llat = np.ravel(yv)
            amp = np.zeros((len(llon),))
            pha = np.zeros((len(llon),))

        # If Necessary, Apply Prime-Meridian Correction (Shift to Range [-180,180])
        if (pm_correct == True):
            print(':: Applying the prime-meridian correction.')
            if wlon > 0.:
                sys.exit('Error: When applying the prime-meridian correction, the longitudes of the bounding box must range from [-180,180].')
            if elon < 0.:
                sys.exit('Error: When applying the prime-meridian correction, the longitudes of the bounding box must range from [-180,180].')
            pm_correction = np.where(llon>=180.); pm_correction = pm_correction[0]
            llon[pm_correction] -= 360.

        # Find Indices Outside Bouding Box
        bboxoutside = np.where((llon <= wlon) | (llat <= slat) | (llon >= elon) | (llat >= nlat)); bboxoutside = bboxoutside[0]

        # Find Indices Inside Bounding Box
        bboxinside = np.where((llon >= wlon) & (llat >= slat) & (llon <= elon) & (llat <= nlat)); bboxinside = bboxinside[0]

        # If Necessary, Shift Longitude Values back to Original Range ([0,360])
        if (pm_correct == True):
            llon[pm_correction] += 360.

        # Set Amplitude and Phase to Constant Values Outside Bounding Box
        if (set_outside == True):
            amp[bboxoutside] = loadamp
            pha[bboxoutside] = loadpha

        # Set Amplitude and Phase to Constant Values Inside Bounding Box
        if (set_inside == True):
            amp[bboxinside] = loadamp
            pha[bboxinside] = loadpha

        # Output OTL Grid to File for Plotting in GMT
        if (write_gmt == True):
            print(":: Writing GMT-convenient text file.")
            custom_out = outfile + ".txt"
            custom_file = ("../../output/Grid_Files/GMT/Custom/height-anomaly_" + custom_out)
            # Prepare Data
            all_custom_data = np.column_stack((llon,llat,amp))
            # Write Data to File
            np.savetxt(custom_file, all_custom_data, fmt='%f %f %f')

        # Output Grid to File for Use with LoadDef
        if (write_nc == True):
            print(":: Writing netCDF-formatted file.")
            custom_out = (outfile + ".nc")
            custom_file = ("D:/06Seasonal/LoadDef_Amite/output/Grid_Files/nc/Custom/convgf_" + custom_out)
            # Open new NetCDF file in "write" mode
            dataset = netCDF4.Dataset(custom_file,'w',format='NETCDF4_CLASSIC')
            # Define dimensions for variables
            num_pts = len(llat)
            latitude = dataset.createDimension('latitude',num_pts)
            longitude = dataset.createDimension('longitude',num_pts)
            amplitude = dataset.createDimension('amplitude',num_pts)
            phase = dataset.createDimension('phase',num_pts)
            # Create variables
            latitudes = dataset.createVariable('latitude',float,('latitude',))
            longitudes = dataset.createVariable('longitude',float,('longitude',))
            amplitudes = dataset.createVariable('amplitude',float,('amplitude',))
            phases = dataset.createVariable('phase',float,('phase',))
            # Add units
            latitudes.units = 'degree_north'
            longitudes.units = 'degree_east'
            amplitudes.units = 'm'
            phases.units = 'degree'
            # Assign data
            latitudes[:] = llat
            longitudes[:] = llon
            amplitudes[:] = amp
            phases[:] = pha
            # Write Data to File
            dataset.close()
        if (write_txt == True):
            print(":: Writing plain-text file.")
            custom_out = (outfile + ".txt")
            custom_file = ("../../output/Grid_Files/text/Custom/convgf_" + custom_out)
            # Prepare Data
            all_custom_data = np.column_stack((llat,llon,amp,pha))
            # Write Data to File
            np.savetxt(custom_file, all_custom_data, fmt='%f %f %f %f')

        # --------------------- END CODE --------------------------- #


# %%
# --------------- SPECIFY USER INPUTS --------------------- #
# Specify Bounding Box for Load Model (e.g. boundingbox.klokantech.com)
#  :: In general, the longitude range should be [0,360]
#  :: In the special case that the bounding box crosses the prime meridian,
#     the range should be [-180,0] for wlon and [0,180] for elon
wlon= -90.9770750 #360.+(-91.2277957) # range [0,360] | If Bounding Box Crosses Prime Meridian, range = [-180,0]
elon= -90.9779771 # 360.+(-91.2172368) # range [0,360] | If Bounding Box Crosses Prime Meridian, range = [0,180]
slat= 30.4378743 #30.3089489  # range [-90,90]
nlat= 30.438776 #30.31811  # range [-90,90]


# Apply Prime-Meridian Correction?
#  :: Set to "True" if the Bounding Box Stradles the Prime Meridian
#  :: Ranges Must be [-180,0] and [0,180]
pm_correct = False

# Specify Load Height (meters)
loadamp=4.84

# Specify Phase (deg)
loadpha=0.0

# Apply the Given Load Height and Phase to the Region Outside the Bounding Box
set_outside = False

# Apply the Given Load Height and Phase to the Region Inside the Bounding Box
set_inside = True

# Optional: Starting Grid File (If no initial starting grid, set "initial_grid = None")
initial_grid = None
regular_grid = True

# Grid Spacing
#  :: Only used if a starting grid file is not supplied
gspace = 0.0005

# Output Filename

outfile = ("AR_load_BRregion_TEST"+str(loadamp)+"_area137")

# Write Load Information to a netCDF-formatted File? (Default for convolution)
write_nc = True

# Write Load Information to a Text File? (Alternative for convolution)
write_txt = True

# Write Load Information to a GMT-formatted File? (Lon, Lat, Amplitude)
write_gmt = False

# ------------------ END USER INPUTS ----------------------- #


# -------------------- BEGIN CODE -------------------------- #

# Check for output of a file
if (write_nc == False) and (write_txt == False) and (write_gmt == False):
    print(":: Error: No output file(s) selected. Options: netCDF, GMT, and/or plain-text.")
    sys.exit()

# Create Folders
if not (os.path.isdir("../../output/Grid_Files/")):
    os.makedirs("../../output/Grid_Files/")
if not (os.path.isdir("../../output/Grid_Files/GMT/")):
    os.makedirs("../../output/Grid_Files/GMT/")
if not (os.path.isdir("../../output/Grid_Files/GMT/Custom/")):
    os.makedirs("../../output/Grid_Files/GMT/Custom/")
if not (os.path.isdir("../../output/Grid_Files/nc/")):
    os.makedirs("../../output/Grid_Files/nc/")
if not (os.path.isdir("../../output/Grid_Files/nc/Custom/")):
    os.makedirs("../../output/Grid_Files/nc/Custom/")
if not (os.path.isdir("../../output/Grid_Files/text/")):
    os.makedirs("../../output/Grid_Files/text/")
if not (os.path.isdir("../../output/Grid_Files/text/Custom/")):
    os.makedirs("../../output/Grid_Files/text/Custom/")

# Read in Starting Grid, or Generate a New Grid
if initial_grid is not None:
    # Read in Starting Grid
    llat,llon,amp,pha,lat1dseq,lon1dseq,amp2darr,pha2darr = read_AmpPha.main(initial_grid,regular_grid=regular_grid)
# Generate New Grid
else:
    lats = np.arange(ext_s, ext_n, gspace) + (gspace/2.0)
    lons = np.arange(ext_w, ext_e, gspace) + (gspace/2.0)
    xv,yv = np.meshgrid(lons,lats)
    llon = np.ravel(xv)
    llat = np.ravel(yv)
    amp = np.zeros((len(llon),))
    pha = np.zeros((len(llon),))

# If Necessary, Apply Prime-Meridian Correction (Shift to Range [-180,180])
if (pm_correct == True):
    print(':: Applying the prime-meridian correction.')
    if wlon > 0.:
        sys.exit('Error: When applying the prime-meridian correction, the longitudes of the bounding box must range from [-180,180].')
    if elon < 0.:
        sys.exit('Error: When applying the prime-meridian correction, the longitudes of the bounding box must range from [-180,180].')
    pm_correction = np.where(llon>=180.); pm_correction = pm_correction[0]
    llon[pm_correction] -= 360.

# Find Indices Outside Bouding Box
bboxoutside = np.where((llon <= wlon) | (llat <= slat) | (llon >= elon) | (llat >= nlat)); bboxoutside = bboxoutside[0]

# Find Indices Inside Bounding Box
bboxinside = np.where((llon >= wlon) & (llat >= slat) & (llon <= elon) & (llat <= nlat)); bboxinside = bboxinside[0]

# If Necessary, Shift Longitude Values back to Original Range ([0,360])
if (pm_correct == True):
    llon[pm_correction] += 360.

# Set Amplitude and Phase to Constant Values Outside Bounding Box
if (set_outside == True):
    amp[bboxoutside] = loadamp
    pha[bboxoutside] = loadpha

# Set Amplitude and Phase to Constant Values Inside Bounding Box
if (set_inside == True):
    amp[bboxinside] = loadamp
    pha[bboxinside] = loadpha


# Output OTL Grid to File for Plotting in GMT
if (write_gmt == True):
    print(":: Writing GMT-convenient text file.")
    custom_out = outfile + ".txt"
    custom_file = ("../../output/Grid_Files/GMT/Custom/height-anomaly_" + custom_out)
    # Prepare Data
    all_custom_data = np.column_stack((llon,llat,amp))
    # Write Data to File
    np.savetxt(custom_file, all_custom_data, fmt='%f %f %f')

# Output Grid to File for Use with LoadDef
if (write_nc == True):
    print(":: Writing netCDF-formatted file.")
    custom_out = (outfile + ".nc")
    custom_file = ("../../output/Grid_Files/nc/Custom/convgf_" + custom_out)
    # Open new NetCDF file in "write" mode
    dataset = netCDF4.Dataset(custom_file,'w',format='NETCDF4_CLASSIC')
    # Define dimensions for variables
    num_pts = len(llat)
    latitude = dataset.createDimension('latitude',num_pts)
    longitude = dataset.createDimension('longitude',num_pts)
    amplitude = dataset.createDimension('amplitude',num_pts)
    phase = dataset.createDimension('phase',num_pts)
    # Create variables
    latitudes = dataset.createVariable('latitude',float,('latitude',))
    longitudes = dataset.createVariable('longitude',float,('longitude',))
    amplitudes = dataset.createVariable('amplitude',float,('amplitude',))
    phases = dataset.createVariable('phase',float,('phase',))
    # Add units
    latitudes.units = 'degree_north'
    longitudes.units = 'degree_east'
    amplitudes.units = 'm'
    phases.units = 'degree'
    # Assign data
    latitudes[:] = llat
    longitudes[:] = llon
    amplitudes[:] = amp
    phases[:] = pha
    # Write Data to File
    dataset.close()
if (write_txt == True):
    print(":: Writing plain-text file.")
    custom_out = (outfile + ".txt")
    custom_file = ("../../output/Grid_Files/text/Custom/convgf_" + custom_out)
    # Prepare Data
    all_custom_data = np.column_stack((llat,llon,amp,pha))
    # Write Data to File
    np.savetxt(custom_file, all_custom_data, fmt='%f %f %f %f')

# --------------------- END CODE --------------------------- #

# %%
