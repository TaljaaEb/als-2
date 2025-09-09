# A_sql_monitor.py
import socket
import json
import time
import random
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- CONFIG ---
C_HOST = "127.0.0.1"  # C server IP
C_PORT = 5000

B_TRIGGER_HOST = "127.0.0.1"  # B listener IP
B_TRIGGER_PORT = 5051

HTTP_PORT = 8000
EVOLUTION_INTERVAL = 10  # seconds

# --- DATA ---
itemlines = [
    "101 18V Cordless Drill 2 89.99",
    "102 6-inch Wood Clamp 4 12.50",
    "103 Carpenter's Hammer 1 19.99"
]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/itemlines":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            for ln in itemlines:
                self.wfile.write(f"<custom>{ln}</custom>\n".encode())

def send_to_c():
    """Send itemlines to C"""
    payload = {"source": "A", "itemlines": itemlines}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((C_HOST, C_PORT))
        s.sendall(json.dumps(payload).encode())
        resp = s.recv(1024)
        print("[A] C responded:", resp.decode())

def trigger_b():
    """Tell B it can start"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((B_TRIGGER_HOST, B_TRIGGER_PORT))
        s.sendall(b"SUCCESS")

def listen_for_checkout():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 6000))
        s.listen(5)
        print("[A] Listening for checkout IPC on 6000...")
        while True:
            conn, addr = s.accept()
            data = conn.recv(1024).decode()
            if data.startswith("CHECKOUT"):
                print("[A] Checkout event:", data)

if __name__ == "__main__":
    #listen_for_checkout()
    print("[A] Static mode, serving HTTP only")
    server = HTTPServer(("0.0.0.0", HTTP_PORT), Handler)
    print(f"[A] HTTP server running on port {HTTP_PORT}...")
    server.serve_forever()
