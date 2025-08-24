#als
"""
FastAPI secure logging sink (C)
- Receives POST /log
- Auth: API Key (Bearer) or mutual TLS (optional)
- Stores raw payloads into SQLite (logs table)
- Minimal dependencies: fastapi, uvicorn

Usage:
  pip install fastapi uvicorn
  python C_backend_fastapi.py --certfile server.crt --keyfile server.key --client-ca ca.crt  # for mTLS (optional)
  python C_backend_fastapi.py --certfile server.crt --keyfile server.key                       # TLS only
  python C_backend_fastapi.py --no-tls                                                    # plain HTTP (not recommended)

See the `# CERT` block at the bottom for example OpenSSL commands to create test certs.
"""

from fastapi import FastAPI, Request, Header, HTTPException, status
from fastapi.responses import JSONResponse
import sqlite3
import os
import argparse
import ssl
import uvicorn
from datetime import datetime
import json
from typing import Optional

DB_PATH = os.environ.get("C_LOG_DB", "c_logs.db")
API_KEYS = {"A": "api_key_for_A_123", "B": "api_key_for_B_456"}  # rotate/replace in prod

app = FastAPI(title="C - Secure Logging Sink")

# --- DB helpers ---
def init_db(path=DB_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        received_at TEXT NOT NULL,
        source TEXT,
        client_ip TEXT,
        headers TEXT,
        payload_raw BLOB
    );
    """)
    conn.commit()
    conn.close()


def append_log(source: Optional[str], client_ip: Optional[str], headers: dict, payload_bytes: bytes):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO logs (received_at, source, client_ip, headers, payload_raw) VALUES (?, ?, ?, ?, ?)",
        (datetime.utcnow().isoformat() + 'Z', source, client_ip, json.dumps(headers), payload_bytes),
    )
    conn.commit()
    conn.close()


# --- Auth dependency ---
async def verify_api_key(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Return source id when API key valid, else raise 401. Accepts header 'Authorization: Bearer <key>'"""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header format")
    key = authorization.split(" ", 1)[1].strip()
    for src, valid_key in API_KEYS.items():
        if key == valid_key:
            return src
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")


# --- Endpoints ---
@app.post("/log")
async def receive_log(request: Request, authorization: Optional[str] = Header(None)):
    # Prefer API key authentication. If mTLS is used, client cert subject could be checked separately.
    source = None
    try:
        source = await verify_api_key(authorization)
    except HTTPException as e:
        # propagate auth errors
        raise e

    client_ip = request.client.host if request.client else None
    headers = dict(request.headers)
    body = await request.body()

    # Append raw payload only; NO processing
    append_log(source, client_ip, headers, body)

    return JSONResponse({"status": "ok", "received_from": source, "bytes": len(body)})


@app.get("/health")
async def health():
    return {"status": "ok", "time_utc": datetime.utcnow().isoformat() + 'Z'}


# --- CLI / TLS config and run ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run C - secure logging sink")
    parser.add_argument("--certfile", help="Path to server certificate (PEM). If omitted and --no-tls not set, server will error.")
    parser.add_argument("--keyfile", help="Path to server key (PEM)")
    parser.add_argument("--client-ca", help="Path to CA cert used to validate client certs (enables mTLS)")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8443)
    parser.add_argument("--no-tls", action="store_true", help="Run without TLS (not recommended)")
    args = parser.parse_args()

    init_db()

    if args.no_tls:
        print("[WARN] Running without TLS. Not recommended for production.")
        uvicorn.run(app, host=args.host, port=args.port)
        raise SystemExit

    if not args.certfile or not args.keyfile:
        raise SystemExit("--certfile and --keyfile are required unless --no-tls is specified")

    # Build SSLContext for optional mTLS
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=args.certfile, keyfile=args.keyfile)

    if args.client_ca:
        # enable client cert verification
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(cafile=args.client_ca)
        print("[INFO] mTLS enabled: server will require client certificate signed by provided CA")
    else:
        print("[INFO] TLS only (no client cert verification)")

    # Run uvicorn with custom SSLContext
    uvicorn.run(app, host=args.host, port=args.port, ssl_context=context)


# -------------------------
# CERT (example OpenSSL commands for local testing)
# -------------------------
# 1) Create a CA:
#   openssl genrsa -out ca.key 4096
#   openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out ca.crt -subj "/CN=Test CA"
#
# 2) Create server key/csr and sign with CA:
#   openssl genrsa -out server.key 2048
#   openssl req -new -key server.key -out server.csr -subj "/CN=localhost"
#   openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365 -sha256
#
# 3) Create a client key/csr and sign with CA (for mTLS):
#   openssl genrsa -out client.key 2048
#   openssl req -new -key client.key -out client.csr -subj "/CN=clientA"
#   openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365 -sha256
#
# Example curl calls:
# TLS + API key:
#   curl -k --header "Authorization: Bearer api_key_for_A_123" \
#        --data '{"sample": "payload"}' https://localhost:8443/log
#
# TLS + mTLS + API key:
#   curl -k --cert client.crt --key client.key --header "Authorization: Bearer api_key_for_A_123" \
#        --data-binary @payload.json https://localhost:8443/log
#
# NOTE: In production use a proper PKI, rotate API keys, protect DB, and run behind a hardened reverse proxy if desired.
