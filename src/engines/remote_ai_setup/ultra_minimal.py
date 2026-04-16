#!/usr/bin/env python3
"""
Ultra-minimal health server for AI cluster
"""

import json
import http.server
import socketserver
import os


class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {
                "status": "healthy",
                "busy": False,
                "current_model": "minimal",
                "hardware": {
                    "gpu": "unknown",
                    "cpu": "available",
                    "memory": "available",
                },
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8122))
    print(f"🚀 Ultra-minimal health server on port {port}")

    with socketserver.TCPServer(("", port), HealthHandler) as httpd:
        httpd.serve_forever()
