# interface use with existing .....

import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- DATA ---
lineitems = [
    "101 18V Cordless Drill 2 89.99",
    "102 6-inch Wood Clamp 4 12.50",
    "103 Carpenter's Hammer 1 19.99"
]

# -------------------------
# Legacy HTTPServer Handler
# -------------------------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/lineitems":   #endpoint
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            for ln in lineitems:
                self.wfile.write(f"<custom>{ln}</custom>\n".encode())  #change to match with b_collector_monitor
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

#def run_http_server(host="0.0.0.0", port=5555): 
#    server_address = (host, port)
#    httpd = HTTPServer(server_address, Handler)
#    print(f"[A] Legacy server at http://{host}:{port}/line-items")
#    httpd.serve_forever()

#def get_line_items():
#    global Handler  # <-- equivalent to exposing legacy do_GET
#    return "\n".join(f"<custom>{ln}</custom>" for ln in lineitems)

# -------------------------
# Runner
# -------------------------
#if __name__ == '__main__':
#    # Start legacy HTTP server in background thread
#    t = threading.Thread(target=run_http_server, daemon=True)
#    t.start()
