"""GET /health -> {"status": "ok"}

Vercel's Python runtime loads the class named `handler` from each file in api/
and serves it as a serverless function. Standard library only (no requirements).
"""
from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"status": "ok"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep serverless logs quiet
        pass
