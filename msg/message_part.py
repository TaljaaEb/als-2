#als 
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import win32serviceutil
import win32service
import win32event

HOST = "127.0.0.1"
PORT_SOCKET = 8888
PORT_HTTP = 8889   # separate port for HTTP fetch

latest_message = ""


# --- Socket listener (receives messages) ---
def socket_listener():
    global latest_message
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT_SOCKET))
    server.listen(5)
    print(f"[SOCKET] Listening on {HOST}:{PORT_SOCKET}")
    while True:
        conn, addr = server.accept()
        data = conn.recv(1024)
        if data:
            latest_message = data.decode("utf-8")
            print(f"[SOCKET] Received: {latest_message}")
        conn.close()


# --- HTTP handler (serves /ipc) ---
class IPCHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global latest_message
        if self.path == "/ipc":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(latest_message.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return  # disable default logging


def http_server():
    server = HTTPServer((HOST, PORT_HTTP), IPCHandler)
    print(f"[HTTP] Listening on http://{HOST}:{PORT_HTTP}/ipc")
    server.serve_forever()


# --- Windows Service ---
class IPCService(win32serviceutil.ServiceFramework):
    _svc_name_ = "IPCBridgeService"
    _svc_display_name_ = "IPC Bridge Service (Socket to HTML)"

    def __init__(self, args):
        super().__init__(args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        threading.Thread(target=socket_listener, daemon=True).start()
        threading.Thread(target=http_server, daemon=True).start()
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(IPCService)
