from flask import Flask, request, jsonify, send_file, Response

import gaurabda as gcal
import json as json
import os as os
import requests

app = Flask(__name__)

gcal.SetFastingSchema(0)


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


# Function to extract attributes from an object
def extract_attributes(obj):
    attributes = {}
    for attr in dir(obj):
        if not attr.startswith('__') and not callable(getattr(obj, attr)):
            attributes[attr] = getattr(obj, attr)
    return attributes





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
    app.run(debug=True)
