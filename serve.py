#!/usr/bin/env python3
"""Serve the app on the network without any backend logic.

  python3 serve.py                 # http://0.0.0.0:8000  (WebGPU only from localhost; WASM multithread thanks to COOP/COEP)
  python3 serve.py --https         # https://0.0.0.0:8443 with a self-signed certificate (WebGPU from other machines after accepting it)
  python3 serve.py --port 9000 --bind 127.0.0.1
"""
import argparse
import http.server
import socket
import ssl
import subprocess
from pathlib import Path

here = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--bind', default='0.0.0.0')
parser.add_argument('--port', type=int, default=None)
parser.add_argument('--https', action='store_true')
args = parser.parse_args()
port = args.port or (8443 if args.https else 8000)


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, '.wasm': 'application/wasm', '.mjs': 'text/javascript', '.js': 'text/javascript', '.onnx': 'application/octet-stream'}

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(here), **kw)

    def end_headers(self):
        # Cross-origin isolation enables SharedArrayBuffer, hence multithreaded WASM in ONNX Runtime Web.
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()


server = http.server.ThreadingHTTPServer((args.bind, port), Handler)
scheme = 'http'
if args.https:
    cert, key = here / 'cert.pem', here / 'key.pem'
    if not cert.exists():
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', str(key), '-out', str(cert), '-days', '3650',
                        '-subj', '/CN=stereo-cloud-compare', '-addext', f'subjectAltName=DNS:localhost,IP:127.0.0.1,IP:{socket.gethostbyname(socket.gethostname())}'], check=True)
        print(f'Self-signed certificate written to {cert}')
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(cert), str(key))
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    scheme = 'https'
try:
    lan = socket.gethostbyname(socket.gethostname())
except OSError:
    lan = '<ip>'
print(f'Serving {here} on {scheme}://{args.bind}:{port}  ->  {scheme}://localhost:{port}/  and  {scheme}://{lan}:{port}/')
if not args.https:
    print('WebGPU is exposed only on localhost over http; other machines get CPU WASM. Use --https (self-signed) for WebGPU over the network.')
server.serve_forever()
