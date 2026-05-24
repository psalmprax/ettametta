#!/usr/bin/env python3
"""
Super minimal health server using only stdlib
"""

import json
import socket
import threading


def handle_client(client_socket):
    try:
        request = client_socket.recv(1024).decode()
        if "GET /health" in request:
            response = """HTTP/1.1 200 OK
Content-Type: application/json

{"status": "healthy", "busy": false, "current_model": "minimal", "hardware": {"gpu": "unknown", "cpu": "available", "memory": "available"}}"""
        else:
            response = """HTTP/1.1 404 Not Found
Content-Type: text/plain

Not Found"""
        client_socket.send(response.encode())
    except Exception:
        pass
    finally:
        client_socket.close()


def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 8122))
    server.listen(5)
    print("🚀 Minimal health server listening on port 8122")

    while True:
        client, addr = server.accept()
        threading.Thread(target=handle_client, args=(client,)).start()


if __name__ == "__main__":
    run_server()
