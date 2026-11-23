"""Serve the signed webhook endpoint for the local queue demo."""
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from queue_core import enqueue

MAX_BODY = 65536


class Receiver(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            self.send_error(404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400)
            return
        if not 0 < size <= MAX_BODY:
            self.send_error(413 if size > MAX_BODY else 400)
            return
        self.connection.settimeout(5)
        try:
            body = self.rfile.read(size)
        except TimeoutError:
            self.send_error(408)
            return
        if len(body) != size:
            self.send_error(400)
            return
        try:
            self.server.accept_event(
                body, self.headers.get("X-Webhook-Timestamp", ""),
                self.headers.get("X-Webhook-Signature", ""),
            )
        except ValueError:
            self.send_error(400, "invalid webhook")
            return
        except Exception:
            self.send_error(503, "intake unavailable")
            return
        self.send_response(202)
        self.send_header("Content-Length", "0")
        self.end_headers()


def main():
    import psycopg

    dsn = os.environ["WEBHOOK_DATABASE_URL"]
    secret = os.environ["WEBHOOK_SIGNING_SECRET"].encode()
    if not secret:
        raise SystemExit("WEBHOOK_SIGNING_SECRET must be nonempty")

    def accept_event(body, timestamp, signature):
        with psycopg.connect(dsn, autocommit=True) as connection:
            return enqueue(connection, body, timestamp, signature, secret)

    with ThreadingHTTPServer(("127.0.0.1", 8080), Receiver) as server:
        server.accept_event = accept_event
        server.serve_forever()


if __name__ == "__main__":
    main()
