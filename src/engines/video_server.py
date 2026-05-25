#!/usr/bin/env python3
"""
Remote HTTP Server for Video Serving
==================================
"""

import http.server
import socketserver
import os

PORT = 3001
VIDEO_DIR = "/tmp"


class VideoHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def start_server():
    os.chdir(VIDEO_DIR)
    with socketserver.TCPServer(("", PORT), VideoHandler) as httpd:
        print(f"Serving {VIDEO_DIR} on http://localhost:{PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    start_server()
