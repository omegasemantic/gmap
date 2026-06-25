#!/usr/bin/env python3
"""
input.py — parse web form input and write gmap.json or codes.json
Usage: python3 input.py "QUERY STRING"

Syntax:
  "destination"
  "destination + start"
  "destination + start 0900"
  "destination + start 0900 MON"
  "destination + start ARR 0900"
  "destination + start ARR 0900 FRI"
  "destination + start 0900 LAST"
  MODE=BUS|TRN|PUB|WLK|CYC|CAR
  CITY=string
  CODE=KEY:PLACEID
  LAST
"""

import sys
import state

VALID_MODES = ['BUS', 'TRN', 'PUB', 'WLK', 'CYC', 'CAR']
VALID_DAYS  = ['MON', 'TUE', 'TUES', 'WED', 'THU', 'THUR', 'FRI', 'SAT', 'SUN']

def parse(raw):
    tokens = raw.strip()
    upper = tokens.upper()

    # --- standalone config commands ---
    if upper.startswith('MODE='):
        m = tokens[5:].strip().upper()
        if m not in VALID_MODES:
            print(f'ERROR: unrecognised mode: {m}')
            sys.exit(1)
        state.write('_MODE', m)
        print(f'_MODE => {m}')
        return

    if upper.startswith('CITY='):
        city = tokens[5:].strip()
        state.write('_CITY', city)
        print(f'_CITY => {city}')
        return

    if upper.startswith('CODE='):
        parts = tokens[5:].strip().split(':', 1)
        if len(parts) != 2:
            print('ERROR: CODE format is CODE=KEY:PLACEID')
            sys.exit(1)
        key, pid = parts
        state.write_code(key.strip().upper(), pid.strip())
        print(f'codes.json: {key.strip().upper()} => {pid.strip()}')
        return

    # --- split on + for destination / start ---
    if '+' in tokens:
        parts = tokens.split('+', 1)
        des_raw   = parts[0].strip()
        start_raw = parts[1].strip()
    else:
        des_raw   = tokens.strip()
        start_raw = None

    # --- parse time/day/flags from start_raw ---
    start_time  = None
    arrive_by   = None
    day         = None
    last        = None
    start_label = None

    if start_raw:
        words = start_raw.split()
        location_words = []
        i = 0
        while i < len(words):
            w = words[i].upper()
            if w == 'LAST':
                last = True
            elif w == 'ARR' and i + 1 < len(words) and words[i+1].isdigit() and len(words[i+1]) == 4:
                arrive_by = words[i+1]
                i += 1
            elif w in VALID_DAYS:
                day = w
            elif w.isdigit() and len(w) == 4:
                start_time = w
            else:
                location_words.append(words[i])
            i += 1
        start_label = ' '.join(location_words) if location_words else None

    # --- write to gmap.json ---
    state.write('_DES',            des_raw)
    state.write('_START_TIME',     start_time)
    state.write('_ARRIVE_BY_TIME', arrive_by)
    state.write('_DAY',            day)
    state.write('_LAST',           last)

    print(f'_DES => {des_raw}')

    if start_raw is not None:
        state.write('_START', start_label)
        print(f'_START => {start_label}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    parse(sys.argv[1])
