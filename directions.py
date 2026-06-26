#!/usr/bin/env python3
"""
directions.py — call Google Directions API
Reads gmap.json via state.py, writes response.json
"""

import json
import os
import sys
import urllib.request
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

import state

GMAPS_KEY     = os.environ.get('GMAPS_API_KEY', '')
RESPONSE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'response.json')
def run():
    d      = state.read_all()
    origin = d.get('_START_ID')
    dest   = d.get('_DES_ID')
    dep    = d.get('_DEP')
    arr    = d.get('_ARR')

    if not origin:
        print('ERROR: _START_ID not set')
        sys.exit(1)
    if not dest:
        print('ERROR: _DES_ID not set')
        sys.exit(1)

    url = ('https://maps.googleapis.com/maps/api/directions/json'
           + '?origin=place_id:'      + origin
           + '&destination=place_id:' + dest
           + '&mode=transit'
           + '&key='                  + GMAPS_KEY)

    if arr:
        url += '&arrival_time=' + str(arr)
    elif dep:
        url += '&departure_time=' + str(dep)

    print('calling Directions API: transit')
    resp = json.loads(urllib.request.urlopen(url).read())

    if resp['status'] != 'OK':
        print(f'ERROR: API returned {resp["status"]}')
        sys.exit(1)

    with open(RESPONSE_FILE, 'w') as f:
        json.dump(resp, f, indent=2)
    print('response.json written')

if __name__ == '__main__':
    run()
