#!/usr/bin/env python3
"""
server.py — web server for gmap project
GET  /            — serve result.html
GET  /result.html — serve result.html
GET  /input.html  — serve input.html
POST /query       — run directions pipeline
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import sys
import subprocess
from urllib.parse import parse_qs

PORT = 8080
BASE = os.path.expanduser('~/projects/gmap')
sys.path.insert(0, BASE)

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
        body   = self.rfile.read(length).decode('utf-8')
        params = parse_qs(body)

        if self.path == '/query':
            query = params.get('q', [''])[0].strip()
            if not query:
                self._redirect('/input.html')
                return

            scripts = ['resolver.py', 'directions.py', 'format.py', 'render.py']

            result = subprocess.run(
                ['python3', os.path.join(BASE, 'input.py'), query],
                cwd=BASE
            )
            if result.returncode != 0:
                self._serve_error('input error')
                return

            for script in scripts:
                result = subprocess.run(
                    ['python3', os.path.join(BASE, script)],
                    cwd=BASE
                )
                if result.returncode != 0:
                    self._serve_error(f'{script} error')
                    return

            self._redirect('/result.html')

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

    def _serve_error(self, msg):
        body = f'<html><body style="font-size:large"><p>ERROR: {msg}</p></body></html>'
        content = body.encode('utf-8')
        self.send_response(500)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    HTTPServer.allow_reuse_address = True
    httpd = HTTPServer(('0.0.0.0', PORT), Handler)
    print(f'Serving on port {PORT}')
    httpd.serve_forever()
