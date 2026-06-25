"""Local development server (standard library only).

Serves the SAME classification logic the Vercel functions use, so the service
can be run and tested locally without the Vercel CLI:

    python server.py            # -> http://localhost:3000
    PORT=8080 python server.py  # custom port

Endpoints:
    GET  /health
    POST /sort-ticket
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import sys

# Make the api/ package importable when run from the backend/ directory.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "api"))

from sort_ticket import parse_and_respond  # noqa: E402


class Router(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"status": "ok"})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/sort-ticket":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            status, body = parse_and_respond(raw)
            self._send(status, body)
        else:
            self._send(404, {"error": "not found"})

    def _send(self, status, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    port = int(os.environ.get("PORT", "3000"))
    server = HTTPServer(("0.0.0.0", port), Router)
    print("Listening on http://localhost:%d  (Ctrl+C to stop)" % port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
