"""Read-only example addon. Replace this service with your own addon."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from client import snapshot

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            payload = snapshot()
            status = 200
        except Exception as error:
            payload, status = {'error': str(error)}, 503
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
