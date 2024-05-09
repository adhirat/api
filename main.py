from flask import Flask, Response, request, jsonify
import gaurabda as gcal
import json as json
import os as os
import io as io
import datetime
import requests

app = Flask(__name__)

gcal.SetFastingSchema(0)

# Function to extract attributes from an object
def extract_attributes(obj,country):
    attributes = {}
    for attr in dir(obj):
        if not attr.startswith('__') and not callable(getattr(obj, attr)):
            key = attr.replace("m_str", "").lower()
            if key == "fullname":
                value = getattr(obj, attr)
                city, zone = value.split(" ("+country+")", 1)
                attributes["city"] = city
                zone, timezone = value.split("Timezone: ", 1)
                attributes["timezone"] = timezone.rstrip(')')
            else:
                attributes[key] = getattr(obj, attr)
    return attributes


# List Time Zones
@app.route('/timezones', methods=['GET'])
def get_timezones():
    timezones = gcal.GetTimeZones()
    return json.dumps(timezones), 200


# Create new location
@app.route('/add_location', methods=['POST'])
def create_location():
    data = request.json
    loc = gcal.GCLocation(data=data)
    return jsonify({'message': 'Location created successfully'}), 201


# Find existing location
@app.route('/listlocations', methods=['GET'])
def list_location():
    result = gcal.FindLocation()
    if result and len(result) > 0:
        loc_list = []
        for location in result[0]:  # Assuming the list of locations is the first element
            loc_dict = {
                'city': location.m_strCity,
                'country': location.m_strCountry,
                'name': location.m_strName,
                'latitude': location.m_fLatitude,
                'longitude': location.m_fLongitude,
                'offset': location.m_fTimezone,
                'tzid': location.m_nTimezoneId,
                'tzname': location.m_strTimeZone
                # Add more attributes as needed
            }
            loc_list.append(loc_dict)
        return jsonify(loc_list), 200
    else:
        return jsonify({"error": "Location not found"}), 404



# List all countries
@app.route('/countries', methods=['GET'])
def get_countries():
    return jsonify(gcal.GetCountries()), 200



# List cities for given country
@app.route('/cities', methods=['GET','POST'])
def get_locations_for_country():
    req_data = None
    if request.method == 'GET':
        req_data = request.args
    elif request.method == 'POST':
        req_data = request.json
        
    gcal.GCLocationList
    cities = gcal.GetLocationsForCountry(req_data.get('country'))
    data = [extract_attributes(obj,req_data.get('country')) for obj in cities]
    json_data = json.dumps(data)
    if cities:
        print(req_data.get('country'))
        print(json_data)
        return json_data, 200
    else:
        return jsonify({'message': 'No cities found for the country'}), 404

# Find existing location
@app.route('/location/<city>', methods=['GET'])
def find_location(city):
    loc = gcal.FindLocation(city)
    #data = [extract_attributes(obj) for obj in loc]
    #json_data = json.dumps(loc)
    if loc:
        # Assuming loc is a single GCLocation object
        loc_dict = {
            'city': loc.m_strCity,
            'country': loc.m_strCountry,
            'name': loc.m_strName,
            'latitude': loc.m_fLatitude,
            'longitude': loc.m_fLongitude,
            'offset': loc.m_fTimezone,
            'tzid': loc.m_nTimezoneId,
            'tzname': loc.m_strTimeZone
            # Add more attributes as needed
        }
        return jsonify(loc_dict), 200
    else:
        return jsonify({"error": "Location not found"}), 404

# Compute Valender Data
@app.route('/calendar', methods=['GET','POST'])
def get_calculate():
    loca = {}
    date = {}
    returntype=''
    period = None
    format = None
    req_data = None
    if request.method == 'GET':
        req_data = request.args
    elif request.method == 'POST':
        req_data = request.json
    else:
        return Flask.make_response('Unknown method', 500)

    loca['city'] = req_data.get('city')
    loca['country'] = req_data.get('country')
    loca['latitude'] = req_data.get('latitude')
    loca['longitude'] = req_data.get('longitude')
    loca['tzname'] = req_data.get('tzname')
    date['year'] = req_data.get('year')
    date['month'] = req_data.get('month')
    date['day'] = req_data.get('day')
    period = req_data.get('period')
    format = req_data.get('format')

    if loca['latitude'] is None and loca['longitude'] is not None \
       or loca['latitude'] is not None and loca['longitude'] is None:
       return Flask.make_response('Either both LATITUDE,LONGITUDE are valid or none of them', 500)

    if loca['city'] is None:
        return Flask.make_response('city: - Name of location must be specified.', 500)

    if loca['country'] is None:
        return Flask.make_response('country: Name of country must be specified.', 500)
    
    if loca['latitude'] is None:
        sp = gcal.FindLocation(city=loca['city'], country=loca['country'])
        if sp is None:
            return Flask.make_response('Location with name \'{}\', country \'{}\' is not found in database.'.format(loca['name'], loca['country']), 500)
        loca['latitude'] = sp.m_fLatitude
        loca['longitude'] = sp.m_fLongitude
        loca['tzname'] = sp.m_strTimeZone
        loca['location'] = sp
    else:
        loca['latitude'] = float(loca['latitude'])
        loca['longitude'] = float(loca['longitude'])
    
    if date['year'] is None:
        date['year'] = datetime.datetime.now().year
    else:
        date['year'] = int(date['year'])

    if date['month'] is None:
        date['month'] = 1
    else:
        date['month'] = int(date['month'])

    if date['day'] is None:
        date['day'] = 1
    else:
        date['day'] = int(date['day'])
    
    if period is None:
        period = 365
    try:
        period = int(period)
    except:
        return Flask.make_response('p: Time period is number of days (integer number).', 500)
    if period<1:
        return Flask.make_response('p: Time period must be greater than 0 days.', 500)
    if period>3653:
        return Flask.make_response('p: Time period must be lower than 3654 days.', 500)
    
    # create calculation engine and calculate
    tc = gcal.TCalendar()
    location = loca.get('location')
    if location is None:
        location = gcal.GCLocation(data={
            'city': loca['city'],
            'country': loca['country'],
            'latitude': loca['latitude'],
            'longitude': loca['longitude'],
            'tzname': loca['tzname']
        })
    tc.CalculateCalendar(location,gcal.GCGregorianDate(year=date['year'], month=date['month'], day=date['day']),period)
    wf = io.StringIO()
    
    # calculate results in various formats
    if format == 'plain' or format == 'txt' or format =='text':
        returntype='text/plain'
        tc.write(wf, format='plain')
    elif format == 'rtf':
        returntype='application/rtf'
        tc.write(wf, format='rtf')
    elif format == 'html':
        returntype='text/html'
        tc.write(wf)
    elif format == 'table_html':
        returntype='text/html'
        tc.write(wf, format='table')
    elif format == 'xml':
        returntype='application/xml'
        tc.write(wf, format='xml')
    else:
        returntype='application/json'
        tc.write(wf, format='json')
            
    return Response(wf.getvalue(), returntype)   , 200
    #return jsonify(repr(tc.writeTableHtml)), 200


@app.route('/data/<tab>', methods=['GET'])
def invoke_api(tab):
    api_url = "https://script.google.com/macros/s/AKfycbzkpefgxqQ6j-tVIDO5cioltw7gbU0B2sM4bRlDeYyMD3pANGDtYEHCXHCTO7mEregu8w/exec?path="+tab
    
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json(), 200
        else:
            return jsonify({"error": "Failed to fetch data from the API"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(port=5001,debug=False,host='0.0.0.0')
