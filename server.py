#!/usr/bin/env python3
"""
server.py — combined web server for map project
GET  /            — serve result.html
GET  /result.html — serve result.html
GET  /input.html  — serve input.html
POST /query       — run directions query
POST /config      — set _CITY or _MODE in etext.json
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import sys
import json
import subprocess
from urllib.parse import parse_qs
import re

PORT = 8080
BASE = os.path.expanduser('~/map')
sys.path.insert(0, BASE)
import state

VALID_MODES = ['BUS', 'TRN', 'PUB', 'WLK', 'CYC', 'CAR']


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path in ('/', '/result.html'):
            self._serve_file('result.html')
        elif self.path == '/input.html':
            self._serve_file('input.html')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        params = parse_qs(body)

        if self.path == '/query':
            query = params.get('q', [''])[0].strip()

            city_match = re.match(r'^city=(.+)$', query, re.IGNORECASE)
            mode_match = re.match(r'^mode=(.+)$', query, re.IGNORECASE)

            if city_match:
                state.write('_CITY', city_match.group(1).strip().title())
                self._redirect('/input.html')
                return
            if mode_match:
                mode = mode_match.group(1).strip().upper()
                state.write('_MODE', mode)
                self._redirect('/input.html')
                return

            subprocess.run(
                ['python3', os.path.join(BASE, 'sms_input.py'), query],
                cwd=BASE
            )
            subprocess.run(
                ['python3', os.path.join(BASE, 'render.py')],
                cwd=BASE
            )
            self._redirect('/result.html')

        elif self.path == '/config':
            city = params.get('city', [''])[0].strip().title()
            mode = params.get('mode', [''])[0].strip().upper()
            if city:
                state.write('_CITY', city)
            if mode and mode in VALID_MODES:
                state.write('_MODE', mode)
            self._redirect('/input.html')

        else:
            self.send_response(404)
            self.end_headers()

    def _redirect(self, location):
        self.send_response(302)
        self.send_header('Location', location)
        self.end_headers()

    def _serve_file(self, filename):
        path = os.path.join(BASE, filename)
        try:
            with open(path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    HTTPServer.allow_reuse_address = True
    httpd = HTTPServer(('0.0.0.0', PORT), Handler)
    print(f'Serving on port {PORT}')
    httpd.serve_forever()
