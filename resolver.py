#!/usr/bin/env python3
"""
resolver.py — resolve _START and _DES to Google place IDs
Reads gmap.json and codes.json, writes _START_ID and _DES_ID to gmap.json
"""

import json
import os
import sys
import urllib.request
import urllib.parse

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
import state

GMAPS_KEY = os.environ.get('GMAPS_API_KEY', '')

def is_place_id(s):
    return s and str(s).startswith('ChIJ')

def geocode(query, city):
    full_query = f'{query} {city}'
    url = ('https://maps.googleapis.com/maps/api/geocode/json?address='
           + urllib.parse.quote(full_query) + '&key=' + GMAPS_KEY)
    resp = json.loads(urllib.request.urlopen(url).read())
    if resp['status'] == 'OK':
        r = resp['results'][0]
        return r['place_id'], r['formatted_address']
    raise ValueError(f'NOT FOUND: {query}')

def resolve(raw):
    """
    Resolve a raw string to (place_id, display_name).
    1. Already a place ID -> return as-is
    2. Check codes.json
    3. Fall back to geocode API
    """
    if not raw:
        return None, None

    # 1. already a place ID
    if is_place_id(raw):
        return raw, raw

    # 2. check codes.json
    codes = state.read_codes()
    key = raw.strip().upper()
    if key in codes:
        val = codes[key]
        if is_place_id(val):
            print(f'{key} => {val} (codes.json)')
            return val, key
        else:
            # plain string in codes.json — geocode it
            raw = val

    # 3. geocode
    d = state.read_all()
    city = d.get('_CITY', 'New Zealand')
    pid, name = geocode(raw, city)
    print(f'{raw} => {pid} ({name})')
    return pid, name

def run():
    d = state.read_all()
    start_raw = d.get('_START')
    des_raw   = d.get('_DES')

    if not des_raw:
        print('ERROR: _DES not set')
        sys.exit(1)

    des_id, des_name = resolve(des_raw)
    state.write('_DES_ID', des_id)
    print(f'_DES_ID => {des_id}')

    if start_raw:
        start_id, start_name = resolve(start_raw)
        state.write('_START_ID', start_id)
        print(f'_START_ID => {start_id}')
    else:
        print('_START not set — skipping')

if __name__ == '__main__':
    run()
