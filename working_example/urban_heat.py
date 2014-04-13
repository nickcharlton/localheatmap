# -*- coding: utf-8 -*-
"""
Created on Sat Apr 12 19:13:32 2014

@author: Edmund
"""
#import pdb
import numpy as np
import matplotlib.path as mpl

def inorout(boundary_latlon, meas):
    """Are lat-lon points in meas contained within the boundary_latlon path?"""
    
    latlon_path = mpl.Path(boundary_latlon)
    meas_inside = latlon_path.contains_points(meas)

    return meas_inside

def demo_inorout():
    """Demonstrate the use of inorout"""
    #Path (latitudes and longitudes) definining a city boundary
    city_boundary_latlon = np.array([\
                            [50.1,-3.4],
                            [50.2, -3.3], 
                            [50.3, -3.2],
                            [50.2,-3.1],
                            [50.1,-3.0],
                            [50.0, -3.2],
                            [49.9,-3.3],
                            ])
                            
    #Measurement latitudes and longitudes
    meas = np.array([\
                [50.1, -3.2], #In
                [50.2,-3.2], #In
                [50.4, -3.2], #Out
                [50.2,-3], #Out
                [50.1,-3], #In (on edge)
                ])
    
    meas_inside = inorout(city_boundary_latlon, meas)
    
    #Sample application
    urban_meas = meas[meas_inside]
    rural_meas = meas[~meas_inside]
    
    print("City boundary:\n{}\n".format(city_boundary_latlon))
    print("Measurements:\n{}\n".format(meas))
    print("Urban measurements:\n{}\n".format(urban_meas))
    print("Rural measurements:\n{}\n".format(rural_meas))
    
    #pdb.set_trace() #Uncomment to examine urban_meas etc

def loxodrome_endpoint(lat1, lon1, distance_km, bearing, 
                       already_radians = None, earthradiuskm = None):
    """
    Get endpoint lat & lon for rhumb line (constant bearing*) route distance_km long on Earth surface (unless tweak earthradiuskm)
    *: clockwise from North == 0, in decimal degrees, unless specify already_radians
    
    Source: http://www.movable-type.co.uk/scripts/latlong.html
    
    """
    
    if earthradiuskm is None: #Then use the authalic/volumetric value at Earth surface
        earthradiuskm = 6371 #km. See http://stackoverflow.com/questions/5283900/what-earth-radius-should-i-use-to-calculate-distances-near-the-poles
    
    #Want to work with arrays internally, but return lat2 & lon2 values in form lat1 came in as (assume same for lon1, distance_km, bearing)
    #If lat1 values come in as a numpy array, return all values as such. If just as a number or list, return as such
    am_numpy_array = am_i_numpy_array(lat1) #Save whether was numpy array originally
    lat1, lon1, distance_km, bearing = map(arrayer, [lat1, lon1, distance_km, bearing]) #Force all to be arrays
        
    #Default: assume decimal degrees (if not specified, None = false so below triggered)
    if not already_radians: # convert decimal degrees to radians 
        lon1, lat1, bearing = map(np.radians, [lon1, lat1, bearing])
    
    alpha = distance_km / np.float(earthradiuskm)
    dlat = alpha * np.cos(bearing)
    lat2 = lat1 + dlat
    stretched_dlat = np.log(np.tan((lat2 + (np.pi/2.0)) / 2.0) / np.tan((lat1 + (np.pi/2.0)) / 2.0))
    
    #pdb.set_trace()
    #For E-W lines, stretched_dlat=0, so want to sanitise
    ok = np.logical_or(stretched_dlat < 0, stretched_dlat > 0)
    q = np.nan * np.ones(dlat.shape)
    q[ok] = dlat[ok] / stretched_dlat[ok]
    q[~ok] = np.cos(lat1[~ok])
    
    dlon = alpha * np.sin(bearing) / q
    lon2 = ((lon1 + dlon + np.pi) % (2 * np.pi)) - np.pi
    
    if not already_radians: #Convert back to decimal degrees
        lat2 , lon2 = map(np.degrees, [lat2, lon2])
    
    #Keep lat2 & lon2 in same form lat1 came in as
    lat2 = form_maintainer(lat2, am_numpy_array)
    lon2 = form_maintainer(lon2, am_numpy_array)
    return lat2, lon2

def demo_loxodrome():
    
    lats = [50.3, 50.1, 49.9, 50.1] 
    lons = [-3.1, -3, -3.1, -3.2]
    distance_km = [10, 10, 10, 10]
    bearings = [0, 90, 180, 270]
    
    out_lats, out_lons = loxodrome_endpoint(lats, lons, distance_km, bearings)
    
    print("Original points:\n{}\n".format(zip(lats,lons)))
    print("Points + 10km N, E, S, W respectively:\n{}\n".format(zip(out_lats,
                                                                    out_lons)))
def arrayer(orig):
    """Convert an input to a numpy array
    Works for input = single value, list, or numpy array
    
    """
    am_numpy_array = am_i_numpy_array(orig)
    if am_numpy_array:
        arrayed_orig = orig #Already arrays
    else: #Need to convert to arrays
        am_list = am_i_list(orig)
        if am_list: #Easy mapping for lists...
            arrayed_orig, = map(np.array, [orig])
        else: #... but single values need cladding
            arrayed_orig, = map(np.array, [[orig]])
    return arrayed_orig

def form_maintainer(arry, orig_is_numpy_array):
    """Return an array in the same form it came in as
    If as a number, a number; list->list;array->array
    
    """
    if orig_is_numpy_array:
        reformed_arry = arry #Don't convert
    else:
        if len(arry) > 1:
            reformed_arry = list(arry)
        else:
            reformed_arry = arry[0]
    return reformed_arry

# Type-checking functions.
# Note this is unpythonic* - done for convenient conversion purposes
# *http://stackoverflow.com/questions/152580/whats-the-canonical-way-to-check-for-type-in-python
def am_i_numpy_array(int_float_list_or_array):
    """Return true if input is a numpy array"""
    #Note numpy imported/shadowed as np above, so ok...
    am_numpy_array = isinstance(int_float_list_or_array, np.ndarray)
    return am_numpy_array

def am_i_list(int_float_list_or_array):
    """Return true if input is a list"""
    am_list = isinstance(int_float_list_or_array, list)
    return am_list

def main():
    demo_inorout()
    demo_loxodrome()

if __name__ == "__main__":
    main()
