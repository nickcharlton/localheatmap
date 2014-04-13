import requests
import urban_heat
import numpy as np
import time
import ast
"""
Functions that returns the boundaries of a city. 
NOTE: This function only works for exeter, uk for the moment
PARAMS
    city: 'exeter'
    state: 'uk'
    
RETURNS:
    List of dictionaries of the form:
        {
            type:'node',
            id: 456788
            lat:50.7374,
            lon:-4.4553
        }
"""
def get_city_boundaries(city,state):
  
    urlLocation = ("http://overpass-api.de/api/interpreter?data=[out:json];" +
    "area[name=%22"+ city +"%22][%22is_in:state_code%22=%22"+ state +"%22];" +
    "foreach(out;);node[name=%22" + city + "%22][%22is_in%22~%22" + state + "%22];" +
    "foreach(out;is_in;out;);") 
    
    jsonLoc = requests.get(urlLocation).json()
    
    id_boundary = str(jsonLoc['elements'][7]['id'])[3:]
    
    urlBoundary = ("http://overpass-api.de/api/interpreter?data=[out:json];" +
    "(relation(" + id_boundary + ");%3E;);out;")

    boundary = requests.get(urlBoundary).json()['elements']
    
    return boundary

"""
Gets the 4 points that are the outer most of a polygon, to create an outer square

PARAMS:
    List of dictionaries of the form:
    {
        lat:34.43534
        lon:45.453534
    }
RETURNS:
"""
def get_most_outer_points_boundary(boundary):
    
    first_point = {"lat":boundary[0]['lat'], "lon":boundary[0]['lon']}

    points = {
        "north":first_point,
        "south":first_point,
        "east":first_point,
        "west":first_point
    }
    
    for node in boundary:
        if node['type'] != 'node':
            continue
            
        if points['north']['lat'] < node['lat']:
            points['north'] = node
        
        if points['south']['lat'] > node['lat']:
            points['south'] = node
        
        if points['east']['lon'] < node['lon']:
            points['east'] = node
        
        if points['north']['lon'] > node['lon']:
            points['west'] = node    
        
    return points

def convTupl2Dict(tupl):
    return {'lat':tupl[0],
            'lon':tupl[1]}

"""
PARAMS:
    pts: 4 point from the outside boundary to build the outer square
    time: time in the format day/month/year hour:minute
    zoom: not sure about this one
Returns:
    List of dictionaries of the form:
    {
        mt:"jtwr",
        mri: 6754364,
        Universal: {},
        Primary:{
            dt: 12,
            dws: 0,
            dh: 63,
            dwd: 315,
            dm: 1023,
            drr: 0.0
        },
        Secondary:{
            dt: 12,
            dws: 0,
            dh: 63,
            dwd: 315,
            dm: 1023,
            drr: 0.0
        },
        msi:8765
        
    }
"""
def get_weather_data(pts,time,zoom):
    center = {
        'lat':'%.5f' % (pts[0]['lat'] - (pts[0]['lat'] - pts[3]['lat'])/2),
        'lon':'%.5f' % (pts[0]['lon'] + (pts[1]['lon'] - pts[0]['lon'])/2)
    }
    
    #time = day/month/year+hour:time
    
    url = ("http://wow.metoffice.gov.uk/ajax/home/map?timePointSlider=24"+
           "&timePointPicker=-1&northLat=" + '%.5f' % pts[0]['lat'] + "&southLat="+ 
           '%.5f' % pts[2]['lat'] + "&eastLon="+ '%.5f' % pts[1]['lon'] +
           "&westLon=" + '%.5f' % pts[0]['lon'] + "&centerLat=" + center['lat'] + 
           "&centerLon=" + center['lon'] + "&zoom=" + zoom +
           "&mapTime=" + time + "&useSlider=false&mapLayer=dry_bulb"+
           "&showWowData=on&showMetOffice")
    
    return requests.get(url).json()['r']


#too messy
def get_inner_outer_weather_data(city_boundaries,data,outer):
    cityBoundList = []
    for node in city_boundaries:
        if node['type'] != 'node':
            continue
        cityBoundList.append([node['lat'],node['lon']])
    
    
    dataList = []
    for node in data:
        dataList.append([float(node['mla']),float(node['mlo'])])
 
    dataList = np.array(dataList)
    cityBoundList = np.array(cityBoundList)
    
    meas_inside = urban_heat.inorout(cityBoundList, dataList)
    
    inside_data = [];
    outside_data = [];
    i = 0
    for inside in meas_inside:
        if inside:
            inside_data.append(data[i])
        else:
            outside_data.append(data[i])
        i += 1
    
    outer_box = []
    for node in outer:
        outer_box.append([node['lat'],node['lon']])
    
    outer_data = []
    for node in outside_data:
        outer_data.append([float(node['mla']),float(node['mlo'])])
    
       
    outer_box = np.array(outer_box)
    outer_data = np.array(outer_data)
   
    print outer_data
    print outer_box
    
    meas_inside = urban_heat.inorout(outer_box, outer_data)
    
    final_outside_data = []
    i = 0
    for inside in meas_inside:
        if inside:
            final_outside_data.append(outside_data[i])
        i += 1
    
    return inside_data,final_outside_data

def order_nodes(stringy):
    """Order the nodes
    Input: the string representation of the json dict of nodes & ways
    Output: a numpy array with the ordered lat, lon pts (also 2 ids - ignore)
    
    """
    
    #String
    interpreter_dict = ast.literal_eval(stringy)
    
    elements = interpreter_dict["elements"]
    
    way_members = elements[-1]["members"]
    
    nodes_dict = {}
    ways_dict = {}
    
    for element in elements[:-1]:
        if element["type"] == "node":
            nodes_dict[element["id"]] = element
        elif element["type"] == "way":
            ways_dict[element["id"]] = element
        else:
            print("Unknown type")
            #pdb.set_trace()        
    
    #pdb.set_trace()
    #Maximum number of points needed should be len(nodes_dict), but isn't.
    #Guess some may be shared? Solution: just double it
    ordered_pts = np.zeros([len(nodes_dict)*2, 4]) 
    ordered_pts.fill(np.nan)
    #pdb.set_trace()
    i = 0
    for way_member in way_members:
        way_id = way_member["ref"]
        for node_id in ways_dict[way_id]["nodes"]:
            node = nodes_dict[node_id]
            ordered_pts[i, 0] = node["lat"]
            ordered_pts[i, 1] = node["lon"]
            ordered_pts[i, 2] = node_id
            ordered_pts[i, 3] = way_id
            i = i + 1
            #pdb.set_trace()
    imin = np.where(np.isnan(ordered_pts[:,0]))[0][0]
        
    chop_ordered_pts = ordered_pts[:imin, :] #REmove any extra Nans
    
    return chop_ordered_pts

def prettify_me(arry):
    """Convert numpy array to the list of dicts we need"""
    lats = arry[:, 0]
    lons = arry[:, 1]
    listy = [{"lat":lat, "lon":lon} for lat, lon in zip(lats, lons)]
    return listy
