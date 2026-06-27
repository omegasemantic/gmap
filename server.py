#!/usr/bin/env python3
"""
server.py — web server for gmap project
GET  /              — serve result.html
GET  /result.html   — serve result.html
GET  /input.html    — serve input.html
GET  /admin         — serve dynamic admin page
POST /query         — run directions pipeline
POST /admin/city    — update _CITY in gmap.json
POST /admin/geocode — geocode address, serve confirmation page
POST /admin/code    — write confirmed code to codes.json
POST /admin/delete  — delete code from codes.json
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import sys
import subprocess
from urllib.parse import parse_qs
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, '.env'))
sys.path.insert(0, BASE)

PORT = int(os.environ.get('GMAP_PORT', 8080))

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path in ('/', '/result.html'):
            self._serve_file('result.html')
        elif self.path == '/input.html':
            self._serve_file('input.html')
        elif self.path == '/admin':
            self._serve_admin()
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

        elif self.path == '/admin/city':
            city = params.get('city', [''])[0].strip().lower()
            if city:
                import state
                state.write('_CITY', city)
            self._redirect('/admin')

        elif self.path == '/admin/geocode':
            code    = params.get('code', [''])[0].strip().upper()
            address = params.get('address', [''])[0].strip()
            if not code or not address:
                self._redirect('/admin')
                return
            import state
            from resolver import geocode
            try:
                d    = state.read_all()
                city = d.get('_CITY', 'New Zealand')
                pid, formatted = geocode(address, city)
                maps_url = f'https://www.google.com/maps/place/?q=place_id:{pid}'
                self._serve_confirm(code, formatted, pid, maps_url)
            except ValueError as e:
                self._serve_error(str(e))

        elif self.path == '/admin/code':
            code = params.get('code', [''])[0].strip().upper()
            pid  = params.get('pid', [''])[0].strip()
            if code and pid:
                import state
                state.write_code(code, pid)
            self._redirect('/admin')

        elif self.path == '/admin/delete':
            code = params.get('code', [''])[0].strip().upper()
            if code:
                import state
                from state import _save, CODES_FILE
                d = state.read_codes()
                d.pop(code, None)
                _save(CODES_FILE, d)
            self._redirect('/admin')

        else:
            self.send_response(404)
            self.end_headers()

    def _serve_admin(self):
        import state
        gmap  = state.read_all()
        codes = state.read_codes()

        gmap_rows = ''.join(
            f'<tr><td>{k}</td><td>{v}</td></tr>'
            for k, v in gmap.items()
        )

        codes_rows = ''.join(
            f'<tr><td>{k}</td><td>{v}</td>'
            f'<td>'
            f'<form action="/admin/delete" method="POST" style="display:inline">'
            f'<input type="hidden" name="code" value="{k}">'
            f'<button type="submit">del</button>'
            f'</form>'
            f'</td></tr>'
            for k, v in sorted (codes.items())
        )

        html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{ font-family: sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; }}
  h2 {{ font-size: 1rem; color: #555; margin: 32px 0 10px; border-bottom: 1px solid #eee; padding-bottom: 6px; }}
  input[type="text"] {{
    padding: 8px 14px; font-size: 1rem;
    border: 1px solid #dfe1e5; border-radius: 20px;
    outline: none; margin-bottom: 8px; width: 100%; box-sizing: border-box;
  }}
  select {{
    padding: 8px 14px; font-size: 1rem;
    border: 1px solid #dfe1e5; border-radius: 20px;
    outline: none; margin-bottom: 8px; background: #fff;
  }}
  button {{
    padding: 7px 20px; font-size: 0.9rem;
    border: none; border-radius: 20px;
    background: #e0e0e0; cursor: pointer;
    margin-right: 4px;
  }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 0.95rem; }}
  td {{ padding: 7px 4px; border-bottom: 1px solid #eee; }}
  td:last-child {{ text-align: right; }}
</style>
</head>
<body>

<h2>City</h2>
<form action="/admin/city" method="POST">
  <input type="text" name="city" placeholder="e.g. auckland" autocomplete="off">
  <button type="submit">set</button>
</form>

<h2>Mode</h2>
<form action="/admin/mode" method="POST">
  <select name="mode">
    <option value="TRN">TRN — train</option>
    <option value="BUS">BUS — bus</option>
  </select>
  <button class="dummy" type="submit" style="color:#bbb">set</button>
</form>

<h2>Add favourite</h2>
<form action="/admin/geocode" method="POST">
  <input type="text" name="code" placeholder="code e.g. HOME" autocomplete="off">
  <input type="text" name="address" placeholder="e.g. 378 Wainui Rd Raglan 3297" autocomplete="off">
  <button type="submit">add</button>
</form>

<h2>State (gmap.json)</h2>
<table>{gmap_rows}</table>

<h2>Favourites (codes.json)</h2>
<table>{codes_rows}</table>

</body>
</html>'''

        content = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_confirm(self, code, formatted, pid, maps_url):
        html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{ font-family: sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; }}
  h2 {{ font-size: 1rem; color: #555; margin: 32px 0 10px; border-bottom: 1px solid #eee; padding-bottom: 6px; }}
  p {{ font-size: 0.95rem; }}
  a {{ color: #1a73e8; }}
  button {{
    padding: 7px 20px; font-size: 0.9rem;
    border: none; border-radius: 20px;
    background: #e0e0e0; cursor: pointer;
    margin-right: 8px;
  }}
</style>
</head>
<body>
<h2>Confirm favourite</h2>
<p><b>Code:</b> {code}</p>
<p><b>Address:</b> {formatted}</p>
<p><b>Place ID:</b> {pid}</p>
<p><a href="{maps_url}" target="_blank">verify on Google Maps</a></p>
<form action="/admin/code" method="POST">
  <input type="hidden" name="code" value="{code}">
  <input type="hidden" name="pid" value="{pid}">
  <button type="submit">confirm</button>
  <a href="/admin"><button type="button">cancel</button></a>
</form>
</body>
</html>'''

        content = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

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
