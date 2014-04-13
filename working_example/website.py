from flask import Flask,render_template,request,url_for,jsonify
import get_boundary as gB
import urban_heat
import time
#import get_boundary;

app = Flask(__name__,static_url_path='/static')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/api')
def api():
    city = request.args.get('city', '')
    state = request.args.get('state', '')
    
    city_boundaries = gB.get_city_boundaries(city,state)
    #outer point boundary
    outPtsBound = gB.get_most_outer_points_boundary(city_boundaries)
    
    dist = 10
    outer_points_outer_boundary = {
        'north':gB.convTupl2Dict(urban_heat.loxodrome_endpoint(outPtsBound['north']['lat'], 
                                              outPtsBound['north']['lon'], 
                                              dist, 0)),
        'south':gB.convTupl2Dict(urban_heat.loxodrome_endpoint(outPtsBound['south']['lat'], 
                                              outPtsBound['south']['lon'], 
                                              dist, 180)),
        'east':gB.convTupl2Dict(urban_heat.loxodrome_endpoint(outPtsBound['east']['lat'], 
                                              outPtsBound['east']['lon'], 
                                              dist, 90)),
        'west':gB.convTupl2Dict(urban_heat.loxodrome_endpoint(outPtsBound['west']['lat'], 
                                              outPtsBound['west']['lon'], 
                                              dist, 270))
    }
    outO = outer_points_outer_boundary
    outer_points_outer_boundary = [{
        'lat':outO['west']['lat'] + outO['north']['lat'] - outO['west']['lat'],
        'lon':outO['west']['lon']
    },{
        'lat':outO['east']['lat'] + outO['north']['lat'] - outO['east']['lat'],
        'lon':outO['east']['lon']
    },{
        'lat':outO['east']['lat'] - outO['east']['lat'] + outO['south']['lat'],
        'lon':outO['east']['lon']
    },{
        'lat':outO['west']['lat'] - outO['west']['lat'] + outO['south']['lat'],
        'lon':outO['west']['lon']
    }]
    
    tim = time.strftime('%d/%m/%Y %H:%M')
    weather_data = gB.get_weather_data(outer_points_outer_boundary,tim,'10')
    
    inner_weather_data, outer_weather_data = gB.get_inner_outer_weather_data(city_boundaries,weather_data,outer_points_outer_boundary)
    

    with open('/home/andres/Documents/spaceApps/app/interpreter','r') as inf:
        stringy = inf.read()
    
    ordered_pts = gB.order_nodes(stringy)
    yep = gB.prettify_me(ordered_pts)
    
    
    return jsonify({
        'city_boundary': yep,
        'outer_boundary': outer_points_outer_boundary,
        'inner_data': inner_weather_data,
        'outer_data': outer_weather_data
    })

if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0')
    

    #    interpreter_dict = ast.literal_eval(inf.read())