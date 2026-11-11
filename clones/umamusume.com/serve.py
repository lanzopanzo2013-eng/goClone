#!/usr/bin/env python3
"""
Tiny static server for the umamusume.com reference clone.

Why this exists instead of `python3 -m http.server`:
  * ThreadingHTTPServer  -> concurrent requests, so the browser's parallel
    fetches and keep-alive connections can never stall the single-threaded
    default server (which makes a preview look "dead").
  * no-store headers     -> edits to index.html show up on reload.
  * binds 0.0.0.0        -> reachable through the sandbox preview proxy.
  * graceful SIGTERM     -> clean restarts on port 8000.

Usage:  python3 serve.py [port]      (default 8000)
"""
import os
import signal
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".md": "text/markdown; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".html": "text/html; charset=utf-8",
    }

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, fmt, *args):  # keep the log tail short and useful
        sys.stdout.write("%s - %s\n" % (self.address_string(), fmt % args))
        sys.stdout.flush()


def main():
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), partial(Handler, directory=ROOT))
    httpd.daemon_threads = True
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt))
    print(f"serving {ROOT} on http://0.0.0.0:{PORT}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("server stopped", flush=True)


if __name__ == "__main__":
    main()
