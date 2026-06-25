#!/usr/bin/env python3
"""
input.py — parse web form input and write gmap.json
Usage: python3 input.py "QUERY STRING"

Syntax:
  "destination"
  "destination + start"
  "destination + start DEP HHMM"
  "destination + start DEP HHMM DAY"
  "destination + start ARR HHMM"
  "destination + start ARR HHMM DAY"
  MODE=TRN|BUS
  CITY=string
  CODE=KEY:PLACEID
"""

import sys
import os
import state
from datetime import datetime, timedelta

VALID_MODES = ['BUS', 'TRN']
VALID_DAYS  = {'MON':0,'TUE':1,'WED':2,'THU':3,'FRI':4,'SAT':5,'SUN':6}

def parse_time(hhmm, day_str=None):
    hour   = int(hhmm[:2])
    minute = int(hhmm[2:])
    if hour > 23 or minute > 59:
        print('ERROR: invalid time')
        sys.exit(1)
    now = datetime.now()
    if day_str:
        days_ahead = (VALID_DAYS[day_str] - now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        target = (now + timedelta(days=days_ahead)).replace(
            hour=hour, minute=minute, second=0, microsecond=0)
    else:
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
    return int(target.timestamp())

def parse(raw):
    tokens = raw.strip()
    upper  = tokens.upper()

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

    if '+' in tokens:
        parts     = tokens.split('+', 1)
        des_raw   = parts[0].strip()
        start_raw = parts[1].strip()
    else:
        des_raw   = tokens.strip()
        start_raw = None

    state.write('_DES', des_raw)
    state.write('_DEP', None)
    state.write('_ARR', None)
    print(f'_DES => {des_raw}')

    if start_raw is not None:
        words          = start_raw.split()
        location_words = []
        time_str       = None
        day_str        = None
        arr_mode       = False
        i = 0
        while i < len(words):
            w = words[i].upper()
            if w in ('DEP', 'ARR'):
                if i + 1 < len(words) and words[i+1].isdigit() and len(words[i+1]) == 4:
                    arr_mode = (w == 'ARR')
                    i += 1
                    time_str = words[i]
                else:
                    print(f'ERROR: {w} must be followed by HHMM e.g. {w} 0900')
                    sys.exit(1)
            elif w in VALID_DAYS:
                if time_str is None:
                    print('ERROR: DAY must follow a time e.g. DEP 0900 THU')
                    sys.exit(1)
                day_str = w
            else:
                location_words.append(words[i])
            i += 1

        start_label = ' '.join(location_words) if location_words else None
        state.write('_START', start_label)
        print(f'_START => {start_label}')

        if time_str:
            ts = parse_time(time_str, day_str)
            if arr_mode:
                state.write('_ARR', ts)
                state.write('_DEP', None)
                print(f'_ARR => {ts}')
            else:
                state.write('_DEP', ts)
                state.write('_ARR', None)
                print(f'_DEP => {ts}')
            if day_str:
                print(f'_DAY => {day_str}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    parse(sys.argv[1])
