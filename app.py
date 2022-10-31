from  flask import Flask, escape, request
from  flask_cors import CORS, cross_origin
import time
from datetime import date, datetime
import json
import requests
from password import getUSGSPassword, getNOAAToken
import pandas as pd
import io
import landsatxplore.api
from dateutil.relativedelta import *
from flask import send_file


app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app)


def callNOAAapi(url, params, header):
    r = requests.get(url, params, headers=header).text
    rawData = pd.read_csv(io.StringIO(r))
    return rawData

def get_v2_data(url, header):
    r = requests.get(url, headers=header).text
    weather_dict = json.loads(r)
    return json.dumps(weather_dict, indent = 4, sort_keys=True)
    

@app.route('/api/getNOAAdata', methods=['POST'])
def getNOAAdata():
    data = json.loads(request.data)

    startDate = data['startDate']
    endDate = data['endDate']
    county = data['county']
    county_fips = county_fips_codes[county]


    token = getNOAAToken()
    creds = dict(token=token)

    weatherStationUrl = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/stations?locationid=FIPS:'+str(county_fips)+'&limit=50'
    weatherStations = get_v2_data(weatherStationUrl, creds)
    weatherStationsDict = json.loads(weatherStations)
    
    stations = []
    for station in weatherStationsDict['results']:
        stationInfo = station['id'].split(':')
        stations.append(stationInfo[1])

    params = {'dataset': 'daily-summaries', \
            'stations': stations,\
            'startDate': startDate, 'endDate': endDate,  \
            'dataTypes': ['AWND', 'PRCP', 'SNOW', 'TAVG', 'WT01', 'TMAX', 'TMIN'], \
            'units': 'standard'}

    url = 'https://www.ncei.noaa.gov/access/services/data/v1'

    urlData = callNOAAapi(url, params, creds)
    # print(urlData)

    # dataHead = urlData.head(10)
    result = {
        'rawData': urlData.to_json(),
        'weatherStationData': weatherStations,
        
    }
    return result

@app.route('/api/getDetection', methods=['POST'])
def getDetection():
    print('Detecting the model')
    bytesOfImage = request.get_data()
    with open('ImageProcessing/image.jpeg', 'wb') as out:
        out.write(bytesOfImage)
    return send_file('./veg_firemap.png', mimetype='image/png')

@app.route('/api/getEarthExplorerData', methods=['POST'])
def getEarthExplorerData():
    data = json.loads(request.data)
    lat = float(data['lat'])
    lon = float(data['lon'])
    startDate = data['startDate']
    endDate = data['endDate']

    # today = date.today()
    # yearAgo = today + relativedelta(years = -1)
    # today = today.strftime('%Y-%m-%d')
    # yearAgo = yearAgo.strftime('%Y-%m-%d')

    password = getUSGSPassword()
    api = landsatxplore.api.API('sukhvir', password)
    scenes = api.search(
        dataset = 'LANDSAT_ETM_C1',
        latitude = lat,
        longitude = lon,
        start_date = startDate,
        end_date = endDate,
        max_cloud_cover = 10
    )
    api.logout()

    result = {
        'scenes': scenes[0:10],
        'totalDataLength': len(scenes),
        # 'startDate': yearAgo,
        # 'endDate': today,
    }
    return result

@app.route('/api/getUSDAFireData', methods=['POST'])
def getUSDAFireData():
    data = json.loads(request.data)
    start_date = data['startDate']
    end_date = data['endDate']
    county = data['county']
    county = county.lower()

    url = "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceFIRESTAT_YRLY_01/MapServer/0/query"
    sqlQuery = f"CREATED_DATE > DATE '{start_date} 00:00:00' and CREATED_DATE < DATE '{end_date} 23:59:59' and COUNTY>0"
    outFields = "OBJECTID, STATE_NAME, COUNTY_NAME, DISCOVER_YEAR, FIRE_SIZE_CLASS, CREATED_DATE,FIRE_NUMBER,TOTAL_ACRES_BURNED,TOPO_LANDFORM_ORIGIN,PRESCRIBED_FIRE,SLOPE, ELEVATION, OTHER_FUEL_MODEL,WIND_SPEED,FIRE_NAME,DISTRICT,POO_LATITUDE, POO_LONGITUDE,STATION_NAME"

    params = {"outSR": "4326",
              "where": sqlQuery,
              "outFields": outFields,
              "f":"json"}
    r = requests.get(url, params)
    text = r.text
    data = json.loads(text)

    result = {
        'data': data
    }
    return result


@app.route('/api/getFirestatData')
def getFirestatData():
    pass

@app.route('/api/getNasaLandsatData', methods=['POST'])
def getNasaLandsatData():
    pass

@app.route('/api/getGoogleEarthEngineData', methods=['POST'])
def getGoogleEarthEngineData():
    pass

@app.route('/api/getModisData', methods=['POST'])
def getModisData():
    pass





county_fips_codes = {
    'Almeda': '06001',
    'Alpine': '06003',
    'Amador': '06005',
    'Butte': '06007',
    'Calvares': '06009',
    'Colusa': '06011',
    'Contra Costa': '06013',
    'Del Norte': '06015',
    'El Dorado': '06017',
    'Fresno': '06019',
    'Glenn': '06021',
    'Humboldt': '06023',
    'Imperial': '06025',
    'Inyo': '06027',
    'Kern': '06029',
    'Kings': '06031',
    'Lake': '06033',
    'Lassen': '06035',
    'Los Angeles': '06037',
    'Madera': '06039',
    'Marin': '06041',
    'Mariposa': '06043',
    'Mendocino': '06045',
    'Merced': '06047',
    'Modoc': '06049',
    'Mono': '06051',
    'Monterey': '06053',
    'Napa': '06055',
    'Nevada': '06057',
    'Orange': '06059',
    'Placer': '06061',
    'Plumas': '06063',
    'Riverside': '06065',
    'Sacramento': '06067',
    'San Benito': '06069',
    'San Bernardino': '06071',
    'San Diego': '06073',
    'San Francisco': '06075',
    'San Joaquin': '06077',
    'San Luis Obispo': '06079',
    'San Mateo': '06081',
    'Santa Barbara': '06083',
    'Santa Clara': '06085',
    'Santa Cruz': '06087',
    'Shasta': '06089',
    'Sierra': '06091',
    'Siskiyou': '06093',
    'Solano': '06095',
    'Sonoma': '06097',
    'Stanislaus': '06099',
    'Sutter': '06101',
    'Tehama': '06103',
    'Trinity': '06105',
    'Tulare': '06107',
    'Tuolumne': '06109',
    'Ventura': '06111',
    'Yolo': '06113',
    'Yuba': '06115',
}




# the code below is just for the flask examples

database = {
    1: 'one',
    2: 'two',
    3: 'three',
    4: 'four'
}

optionSelected = None

@app.route('/')
def index():
    return 'This is the flask backend for the wildfire project'

@app.route('/api/time')
def get_current_time():
    return {'time': time.time()}

@app.route('/api/handle-select', methods=['POST'])
def handle_select():
    global optionSelected
    data = json.loads(request.data)
    optionSelected = data['optionSelected']
    return {'optionSelected': optionSelected}

@app.route('/api/get-select')
def get_select():
    global optionSelected
    return {'optionSelected': optionSelected}

@app.route('/api/sum')
def sum():
    num1 = request.args['num1']
    num2 = request.args['num2']

    if(num1 == '' or num2 == ''):
        return {'sum': 'Please enter a value for both numbers'}

    result = calculateSum(float(num1), float(num2))
    return {'sum': result}

def calculateSum(num1, num2):
    return num1 + num2


@app.route('/api/database/<index>')
def indexDatabase(index):
    global database
    index = int(index)
    if index >= len(database) or index < 1:
        return {'result':"No entry at index "+ str(index)}
    return {'result': database[index]}



if __name__ == '__main__':
    app.run(host="0.0.0.0", threaded=True, port=5000)