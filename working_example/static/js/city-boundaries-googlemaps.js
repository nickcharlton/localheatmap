/**
 * Small script to draw boundaries of a city on google maps.
 *
 * Retrieves city boundary data from openstreetmap
 * http://wiki.openstreetmap.org/wiki/Overpass_API
 *
 * @author Peter Kelley, August 12 2013
 */

var BOUNDARY_COLORS = ['FF0000'];
var BOUNDARY_COLOR_COORDINATES_PARAM = 0;

var map;
var allOverlays = [];
var lengendContent = [];

var GRADIENT = ['#031AD8',
                '#1F33DC',
                '#3B4CE0',
                '#5766E5',
                '#737FE9',
                '#8F99ED',
                '#ABB2F2',
                '#C7CCF6',
                '#E3E5FA',
                '#FFFFFF',
                '#FBE5E6',
                '#F8DBDD',
                '#F4C0C3',
                '#F0A5A9',
                '#ED8F93',
                '#E97378',
                '#E5575D',
                '#E03B42',
                '#DC1F27',
                '#DC1F27'
                ];

google.maps.event.addDomListener(window, 'load', initialize); 
function get_color(temp) {
    var min = -20,
        max = 40,
        interval = max - min,
    
    rural_av_temp = 13 // Fake rural temperature - need to wok out average
    //rural_av_temp = 0 !No offset (normal temperatures)
    index = Math.round(( (temp - rural_av_temp) + min)/interval*21)*-1;

    return GRADIENT[21-index];
        
        
        
}
/**
 * Find the city boundaries and display on the google map.
 *
 */
function loadCityLimits() {
	// clear any previous polygons
	while (allOverlays[0]) {
		allOverlays.pop().setMap(null);
	}
	lengendContent = [];
	map.controls[google.maps.ControlPosition.RIGHT_TOP].clear();

	var cityText = document.getElementById('cityTextInput');
	var splitCity = cityText.value.split(",");

	if (splitCity.length != 2) {
		alert("Must enter a city in the format: CITY, STATE.");
		return;
	}

	var city = toTitleCase(splitCity[0].trim());
	var state = splitCity[1].trim().toUpperCase();

    
	var legendContents = [];

	var params = [];
	params[BOUNDARY_COLOR_COORDINATES_PARAM] = BOUNDARY_COLORS[0];
	getRequestJSON(getOSMAreaForCityURL(city, state), constructMapFromBoundaries, params);

	var cityLegend = [city + ", " + state, params[BOUNDARY_COLOR_COORDINATES_PARAM]];
	legendContents.push(cityLegend);

	addLegend(legendContents);
}

/**
 * Add a legend to the google map. This iterates through the legendContents
 * and creates legend entries for each elements of the array.
 *
 * @param {Array} legendContents array of the legend contents to to following
 * 		specifications:
 * legendContents[i][0] - Name of the legend entry
 * legendContents[i][1] - The color for the entry
 *
 * i specifies the entry number
 *
 */
function addLegend(legendContents) {
	// Create the legend and display on the map
	// https://developers.google.com/fusiontables/docs/samples/legend
	var legend = document.createElement('div');
	legend.id = 'legend';
	lengendContent.unshift('<h3>Cities</h3>');
	for (x in legendContents) {
		lengendContent.push('<p><div class="color color' + legendContents[x][1] + '"></div>' + legendContents[x][0] + '</p>');
	}
	legend.innerHTML = lengendContent.join('');
	legend.index = 1;
	map.controls[google.maps.ControlPosition.RIGHT_TOP].push(legend);
}

/**
 * When the window has loaded, do basic initilization including
 * AJAX setup and Google maps set up including setting the 
 * focus on the continental US
 */
function initialize() {
	$("#loading").hide();
	setUpAjax();
	
	var mapOptions = {
		zoom : 4,
		center : new google.maps.LatLng(37.09024, -95.712891),
		streetViewControl : false,
		mapTypeId : google.maps.MapTypeId.ROADMAP
	};
	map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);
}

/**
 * Get the OpenStreetMap URL for the area of a city.
 *
 * @param {String} cityName Name of the city to retrieve the area for
 * @param {String} stateName Name of the state to retrieve the area for
 */
function getOSMAreaForCityURL(cityName, stateName) {
	return "/api?city=" + cityName + '&state=' + stateName;
	// case insensitive, really slow!
	// area[name~%22" + cityName +
	// "%22, i][%22is_in:state_code%22~%22" + stateName + "%22, i];foreach(out;);node[name~%22" + cityName +
	// "%22, i][%22is_in%22~%22" + stateName + "%22];foreach(out;is_in;out;);
	// could directly ping for relation
	//rel[name=Boston]["is_in:state_code"~MA];foreach(out;);
}

/**
 * Get the OpenStreetMap URL for a specific relation.
 *
 * @param {String} relationID ID of the relation to retrieve
 */
function getOSMCityRelationURL(relationID) {
	return "http://overpass-api.de/api/interpreter?data=[out:json];(relation(" + relationID + ");>;);out;";
}

/**
 * Get the relation ID from the area JSON, request the relation and
 * construct the city boundaries from it.
 *
 * @param {JSON} areaJSON JSON area response from OSM
 * @param {Array} params list of any parameters to pass on to
 * 			city boundary callback constructMapFromBoundaries
 */
function processCityArea(areaJSON, params) {
	for (x in areaJSON.elements) {
		// if find something that is level 8
		// if find something labelled city
		// if find something that has the exact name
		if ((areaJSON.elements[x].tags.admin_level == "8" && 
				areaJSON.elements[x].tags.border_type == null) || 
				areaJSON.elements[x].tags.border_type == "city") {
			var areaID = areaJSON.elements[x].id;
			// transform to relation id, and get relation
			var relationID = areaID - 3600000000;

			getRelationInOrder(relationID, constructMapFromBoundaries, params);
			return;
		}
	}
	alert("Couldn't retrieve the city limits for a city, they are either missing from OpenStreetMap, not labeled " + 
		"consistently or the city entered is not valid.");
	console.log("Failed to find city border from OSM.");
}

/**
 * Construct the polygons on the google map from the paths
 * and parameters specified. This is a callback that accepts
 * the parameters given to getRelationInOrder.
 *
 * @param {Array} paths Array of paths, which are an array of
 * 		OSM nodes.
 * @param {Array} params The parameters given to getRelationInOrder.
 * 		Of the format:
 *			params[BOUNDARY_COLOR_COORDINATES_PARAM]; - Color to
 * 			make the polygon.
 */
function constructMapFromBoundaries(jsonObj, params) {
	var color = "#6B6B69",
	    city_boundary = jsonObj.city_boundary,
	    inner_data = jsonObj.inner_data,
	    outer_boundary = jsonObj.outer_boundary,
	    outer_data = jsonObj.outer_data,
	    paths = [],
	    i;
    
	for (var i in city_boundary) {   
		paths.push(new google.maps.LatLng(city_boundary[i].lat, city_boundary[i].lon));
		
	}
    
	// google maps api can create multiple polygons with one create call
	// and returns one object. Also can handle inner ways (holes)
	var polygon = createPolygon(paths, color);

	// set map zoom and location to new polygons
	map.fitBounds(polygon.getBounds());
	
	
	var rectangle = new google.maps.Rectangle({
        strokeColor: '#D7D3E0',
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: '#D7D3E0',
        fillOpacity: 0.35,
        map: map,
        bounds: new google.maps.LatLngBounds(
            new google.maps.LatLng(outer_boundary[0].lat, outer_boundary[0].lon),
            new google.maps.LatLng(outer_boundary[2].lat,outer_boundary[2].lon))
        });
    
    for (var j in inner_data) {
        var data = inner_data[j];
        var color = get_color(+data.Primary.dt);
        new google.maps.Circle({
            center: new google.maps.LatLng(data.mla,data.mlo),
            map: map,
            strokeColor:color,
            strokeOpacity:0.7,
            strokeWeight:2,
            fillColor:color,
            fillOpacity:0.7,
            title:"Hello World!",
            radius:200
        });
    }
    
    for (var k in outer_data) {
        var data2 = outer_data[k];
        var color = get_color(+data2.Primary.dt);
        new google.maps.Circle({
            center: new google.maps.LatLng(data2.mla,data2.mlo),
            map: map,
            strokeColor:color,
            strokeOpacity:0.7,
            strokeWeight:2,
            fillColor:color,
            fillOpacity:0.7,
            title:"Hello World!",
            radius:200
        });
    }
    
	
}

/**
 * Create a polygon on the google map of the specified
 * paths and color.
 *
 * @param {Array} paths Array of coordinates (google.maps.LatLng)
 * 		for this polygon
 * @param {String} The hex value for the color of the polygon,
 * 		omitting the # character
 */
function createPolygon(paths, color) {
	newPolygon = new google.maps.Polygon({
		paths : paths,
		strokeColor : "#" + color,
		strokeOpacity : 0.8,
		strokeWeight : 2,
		fillColor : "#" + color,
		fillOpacity : 0.35,
		draggable : true
		// geodisc: true
	});

	newPolygon.setMap(map);

	allOverlays.push(newPolygon);

	return newPolygon;
}