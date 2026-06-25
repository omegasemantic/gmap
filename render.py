#!/usr/bin/env python3
"""
render.py — reads output.json, writes result.html
"""

import json
import os

OUTPUT_FILE = os.path.expanduser('~/projects/gmap/output.json')
RESULT_FILE = os.path.expanduser('~/projects/gmap/result.html')

def run():
    data = json.load(open(OUTPUT_FILE))

    if 'error' in data:
        html = '<html><body style="font-size:large"><p>NO ROUTE FOUND</p></body></html>'
    else:
        s     = data['summary']
        lines = []
        lines.append(f'<b>{s["destination"]} arr {s["arrival"]} {s["duration"]}</b>')

        for leg in data['legs']:
            lines.append(
                f'{leg["mode"]} {leg["line"]}<br>'
                f'ON {leg["board_time"]} {leg["board"]}<br>'
                f'OFF {leg["alight_time"]} {leg["alight"]}'
            )

        if data.get('final_walk'):
            lines.append(
                f'WALK {data["final_walk"]}<br>'
                f'{data["walk_distance"]}m {data["walk_duration"]}'
            )

        body = '<br><br>'.join(lines)
        html = f'<html><body style="font-size:large"><p>{body}</p></body></html>'

    with open(RESULT_FILE, 'w') as f:
        f.write(html)
    print('result.html written')

if __name__ == '__main__':
    run()
