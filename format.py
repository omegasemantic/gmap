#!/usr/bin/env python3
"""
format.py — extract and structure directions from response.json
Writes output.json for render.py
"""

import json
import os
import re
from datetime import datetime

import state
BASE = os.path.dirname(os.path.abspath(__file__))
RESPONSE_FILE = os.path.join(BASE, 'response.json')
OUTPUT_FILE   = os.path.join(BASE, 'output.json')
WALK_THRESHOLD = 200

ABBREV = [
    (r'\bStreet\b', 'St'),
    (r'\bRoad\b',   'Rd'),
    (r'\bAvenue\b', 'Ave'),
    (r'\bDrive\b',  'Dr'),
    (r'\bPlace\b',  'Pl'),
    (r'\bTerrace\b','Tce'),
]

def abbreviate(s):
    for pattern, replacement in ABBREV:
        s = re.sub(pattern, replacement, s)
    return s

def to_24hr(time_str):
    time_str = time_str.replace('\u202f', ' ').strip()
    try:
        return datetime.strptime(time_str, '%I:%M %p').strftime('%H%M')
    except:
        return time_str

def first_road(stop_name):
    name = stop_name.split(' - ')[0].strip()
    name = re.sub(r',\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?=\s*(?:\(|$))', '', name).strip()
    return abbreviate(name.split('/')[0].strip())

def short_line(name):
    return name.split(' - ')[0].strip()

def dur_mins(text):
    hours = re.search(r'(\d+)\s*hour', text)
    mins  = re.search(r'(\d+)\s*min', text)
    total = 0
    if hours: total += int(hours.group(1)) * 60
    if mins:  total += int(mins.group(1))
    return f'{total}m'

def vehicle_code(td):
    vtype = td['line']['vehicle']['type']
    if 'RAIL' in vtype:
        return 'TRN'
    return vtype[:3]

def final_walk(steps):
    if steps and steps[-1]['travel_mode'] == 'WALKING':
        step = steps[-1]
        dist = step.get('distance', {}).get('value', 0)
        dur  = step.get('duration', {}).get('text', '')
        instr = re.sub('<[^>]+>', ' ', step.get('html_instructions', ''))
        instr = re.sub(r'\s+', ' ', instr).strip()
        instr = instr.replace('Walk to ', '').split(',')[0].strip()
        return abbreviate(instr), dist, dur
    return None, 0, None

def run():
    resp = json.load(open(RESPONSE_FILE))
    d    = state.read_all()

    if resp['status'] != 'OK':
        json.dump({'error': 'NO ROUTE FOUND'}, open(OUTPUT_FILE, 'w'), indent=2)
        return

    leg       = resp['routes'][0]['legs'][0]
    all_steps = leg['steps']

    des_raw   = d.get('_DES', '')
    des_label = des_raw.upper()

    arr = to_24hr(leg['arrival_time']['text'])
    dur = dur_mins(leg['duration']['text'])

    transit_steps = [s for s in all_steps if s['travel_mode'] == 'TRANSIT']
    walk_dest, walk_dist, walk_dur = final_walk(all_steps)

    legs = []
    for step in transit_steps:
        td = step['transit_details']
        legs.append({
            'mode':        vehicle_code(td),
            'line':        short_line(td['line'].get('short_name') or td['line'].get('name', '')),
            'board':       first_road(td['departure_stop']['name']),
            'board_time':  to_24hr(td['departure_time']['text']),
            'alight':      first_road(td['arrival_stop']['name']),
            'alight_time': to_24hr(td['arrival_time']['text']),
        })

    output = {
        'summary': {
            'destination': des_label,
            'arrival':     arr,
            'duration':    dur,
        },
        'legs':           legs,
        'final_walk':     walk_dest if walk_dist > WALK_THRESHOLD else None,
        'walk_distance':  walk_dist if walk_dist > WALK_THRESHOLD else None,
        'walk_duration':  walk_dur  if walk_dist > WALK_THRESHOLD else None,
    }

    json.dump(output, open(OUTPUT_FILE, 'w'), indent=2)
    print('output.json written')

if __name__ == '__main__':
    run()
