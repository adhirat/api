from flask import Flask, request, jsonify, send_file, Response

import gaurabda as gcal
import json as json
import os as os
import requests
import io as io

app = Flask(__name__)

gcal.SetFastingSchema(0)

# Function to extract attributes from an object
def extract_attributes(obj):
    attributes = {}
    for attr in dir(obj):
        if not attr.startswith('__') and not callable(getattr(obj, attr)):
            attributes[attr] = getattr(obj, attr)
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
@app.route('/locations/<country>', methods=['GET'])
def get_locations_for_country(country):
    gcal.GCLocationList
    cities = gcal.GetLocationsForCountry(country)
    data = [extract_attributes(obj) for obj in cities]
    json_data = json.dumps(data)
    if cities:
        print(country)
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


# Print Dates
@app.route('/printdates/<selectedDate>', methods=['GET'])
def get_dates(selectedDate):
    today = gcal.Today()
    print("Today::>  "+repr(today))
    date1 = gcal.GCGregorianDate(text=selectedDate)
    print("Date::>  "+repr(date1))
    return jsonify("Dates printed"), 200

# Compute Valender Data
@app.route('/calculate/<location>/<format>', methods=['GET'])
def get_calculate(location,format):
     # Delete any file with the name 'calendar'
    for file_name in os.listdir():
        if file_name.startswith('calendar'):
            os.remove(file_name)
            
            
    today = gcal.Today()
    loc = gcal.FindLocation(city=location)
    # create calculation engine and calculate
    tc = gcal.TCalendar()
    tc.CalculateCalendar(loc,today,365)
    filename=''
    returntype=''
    #print(tc)
    # save results in various formats
    if format == 'plain':
        filename='calendar.txt'
        returntype='text/plain'
        with open(filename, 'wt') as wf:
            tc.write(wf, format='plain')
    elif format == 'rtf':
        filename='calendar.rtf'
        returntype='application/rtf'
        with open(filename, 'wt') as wf:
            tc.write(wf, format='rtf')
    elif format == 'html':
        filename='calendar.html'
        returntype='text/html'
        with open(filename, 'wt') as wf:
            tc.write(wf)
    elif format == 'table_html':
        filename='calendar.html'
        returntype='text/html'
        with open(filename, 'wt') as wf:
            tc.write(wf, layout='table')
    elif format == 'json':
        filename='calendar.json'
        returntype='application/json'
        with open(filename, 'wt') as wf:
            tc.write(wf, format='json')
    elif format == 'xml':
        filename='calendar.xml'
        returntype='application/xml'
        with open(filename, 'wt') as wf:
            tc.write(wf, format='xml')
    else:
        filename='calendar.json'
        returntype='application/json'
        with open(filename, 'wt') as wf:
            tc.write(wf, format='json')
            
    return send_file(filename, mimetype=returntype, as_attachment=True)   , 200
    #return jsonify(repr(tc.writeTableHtml)), 200


@app.route('/calendar', methods=['GET','POST'])
def getCalendar():
    loca = {}
    date = {}
    period = None
    fmt = None
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
    fmt = req_data.get('format')
    
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

    if loca['tzname'] is None:
        return Flask.make_response('tz: Name of timezone must be specified.', 500)
    
    if date['year'] is None:
        d = io.Today()
        date['year'] = d.year
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
        return Flask.make_response('p: Time period must be specified.', 500)
    try:
        period = int(period)
    except:
        return Flask.make_response('p: Time period is number of days (integer number).', 500)
    if period<1:
        return Flask.make_response('p: Time period must be greater than 0 days.', 500)
    if period>3653:
        return Flask.make_response('p: Time period must be lower than 3654 days.', 500)

    tc = gcal.TCalendar()
    date2 = gcal.GCGregorianDate(year=date['year'], month=date['month'], day=date['day'])
    location = loca.get('location')
    if location is None:
        location = gcal.GCLocation(data={
            'city': loca['city'],
            'country': loca['country'],
            'latitude': loca['latitude'],
            'longitude': loca['longitude'],
            'tzname': loca['tzname']
        })
    tc.CalculateCalendar(location,date2,period)

    wf = io.StringIO()

    # save results in various formats
    if fmt == 'txt' or fmt=='text' or fmt=='plain':
        tc.write(wf, format='plain')
        return Response(wf.getvalue(), mimetype='text/plain')
    elif fmt=='html':
        tc.write(wf)
        return Response(wf.getvalue(), mimetype='text/html')
    elif fmt=='html-table':
        tc.write(wf, layout='table')
        return Response(wf.getvalue(), mimetype='text/html')
    elif fmt=='xml':
        tc.write(wf, format='xml')
        return Response(wf.getvalue(), mimetype='text/xml')
    else:
        return jsonify(tc.get_json_object())


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
