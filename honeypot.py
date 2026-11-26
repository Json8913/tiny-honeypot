#!/usr/bin/env python3
"""A low-interaction HTTP decoy for an isolated lab or authorised network."""

import argparse
from datetime import datetime, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
from urllib.parse import urlsplit


def safe_path(request_target: str) -> str:
    """Return the path only, so query-string values never enter the event log."""
    return urlsplit(request_target).path or "/"


def event_record(client, method: str, path: str, body_bytes: int = 0) -> dict:
    return {
        "time": datetime.now(timezone.utc).isoformat(),
        "event": "http_request",
        "source_ip": client[0],
        "source_port": client[1],
        "method": method,
        "path": safe_path(path),
        "body_bytes": body_bytes,
    }


def log_event(client, method: str, path: str, body_bytes: int = 0) -> None:
    print(json.dumps(event_record(client, method, path, body_bytes)), flush=True)


class HoneypotHandler(BaseHTTPRequestHandler):
    server_version = "Northstar-Portal/1.0"
    sys_version = ""

    def log_message(self, _format: str, *args) -> None:
        # Keep the standard logger from recording request lines or query values.
        return

    def do_GET(self) -> None:
        path = safe_path(self.path)
        log_event(self.client_address, "GET", path)
        title = escape(self.server.portal_title)
        body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    body {{ margin: 0; background: #eef2f6; color: #172331; font: 16px system-ui, sans-serif; }}
    main {{ max-width: 390px; margin: 10vh auto; padding: 30px; background: white; border: 1px solid #d8e0e8; border-radius: 10px; }}
    h1 {{ font-size: 1.4rem; margin-top: 0; }}
    label {{ display: block; margin: 16px 0 6px; }}
    input {{ box-sizing: border-box; width: 100%; padding: 10px; border: 1px solid #aebac7; border-radius: 5px; }}
    button {{ margin-top: 20px; padding: 10px 15px; color: white; background: #244e72; border: 0; border-radius: 5px; }}
    small {{ display: block; margin-top: 18px; color: #596979; }}
  </style>
</head>
<body>
  <main>
    <h1>{title}</h1>
    <p>Sign in to continue to the operations workspace.</p>
    <form method="post" action="/session">
      <label for="username">Username</label>
      <input id="username" name="username" autocomplete="username">
      <label for="password">Password</label>
      <input id="password" name="password" type="password" autocomplete="current-password">
      <button type="submit">Sign in</button>
    </form>
    <small>Use only the approved test environment for this service.</small>
  </main>
</body>
</html>""".encode("utf-8")
        self._reply(200, body, "text/html; charset=utf-8")

    def do_POST(self) -> None:
        # Do not read or log the body, headers, cookies, or query string.
        length_header = self.headers.get("Content-Length", "0")
        try:
            body_bytes = max(0, int(length_header))
        except ValueError:
            body_bytes = 0
        path = safe_path(self.path)
        log_event(self.client_address, "POST", path, body_bytes)
        self.close_connection = True
        body = b"<!doctype html><title>Request received</title><p>Session could not be verified.</p>"
        self._reply(401, body, "text/html; charset=utf-8")

    def _reply(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1",
                        help="bind address; use a lab interface address for an approved network test")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--title", default="Northstar Operations Portal",
                        help="fictional portal title shown on the decoy page")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    server = ThreadingHTTPServer((args.host, args.port), HoneypotHandler)
    server.daemon_threads = True
    server.portal_title = args.title
    print(json.dumps({
        "event": "listening",
        "host": args.host,
        "port": server.server_address[1],
        "title": args.title,
    }), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('{"event":"stopped"}', flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
