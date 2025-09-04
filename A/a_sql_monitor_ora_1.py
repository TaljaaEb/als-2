#a_sql_monitor_ora_1.py

import oracledb
import time

# Database connection details
dsn = oracledb.makedsn("your_host", "your_port", service_name="your_service_name")
connection = oracledb.connect(user="your_username", password="your_password", dsn=dsn)

#
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
# --- DATA ---
itemlines = [
    "101 18V Cordless Drill 2 89.99",
    "102 6-inch Wood Clamp 4 12.50",
    "103 Carpenter's Hammer 1 19.99"
]
#
# -------------------------
# Legacy HTTPServer Handler
# -------------------------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/itemlines":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            for t in itemlines:
                self.wfile.write(f"<custom>{t}</custom>\n".encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

#History
def monitor_transactions():
    try:
        with connection.cursor() as cursor:
            # Query to fetch recent transactions
            query = """
                SELECT transaction_id, user_id, product_id, amount, status, transaction_date
                FROM ecommerce_transactions
                WHERE transaction_date >= SYSDATE - INTERVAL '1' MINUTE
                ORDER BY transaction_date DESC
            """
            while True:
                print("Fetching recent transactions...")
                cursor.execute(query)
                rows = cursor.fetchall()
                
                if rows:
                    for row in rows:
                        print(f"Transaction ID: {row[0]}, User ID: {row[1]}, Product ID: {row[2]}, "
                              f"Amount: {row[3]}, Status: {row[4]}, Date: {row[5]}")
                        #itemlines.append(....)
                else:
                    print("No new transactions in the last minute.")
                
                # Wait for a minute before checking again
                time.sleep(60)
    except oracledb.DatabaseError as e:
        print(f"Database error occurred: {e}")
    finally:
        connection.close()

# Start monitoring
monitor_transactions()

#
def run_http_server(host="0.0.0.0", port=5051): #match b_collector_monitor.py
    server_address = (host, port)
    httpd = HTTPServer(server_address, Handler)
    print(f"[A] Legacy server at http://{host}:{port}/itemlines")
    httpd.serve_forever()

# -------------------------
# Runner
# -------------------------
if __name__ == '__main__':
    # Start legacy HTTP server in background thread
    t = threading.Thread(target=run_http_server, daemon=True)
    t.start()



