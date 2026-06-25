"""
state.py — gmap.json and codes.json read/write functions
"""
import json
import os

STATE_FILE = os.path.expanduser('~/projects/gmap/gmap.json')
CODES_FILE = os.path.expanduser('~/projects/gmap/codes.json')

def _load(path):
    with open(path) as f:
        return json.load(f)

def _save(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

# --- gmap.json ---
def read_all():
    return _load(STATE_FILE)

def read(key):
    return read_all().get(key)

def write(key, value):
    d = read_all()
    d[key] = value
    _save(STATE_FILE, d)

# --- codes.json ---
def read_codes():
    return _load(CODES_FILE)

def read_code(key):
    return read_codes().get(key.upper())

def write_code(key, value):
    d = read_codes()
    d[key.upper()] = value
    _save(CODES_FILE, d)
