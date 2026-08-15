#!/usr/bin/env python3
"""Static server that honours Range requests.

python3 -m http.server cannot do this, and without a 206 the browser has to
download the whole clip before it can seek — which defeats scroll scrubbing
entirely. Usage: serve.py [port]
"""
import http.server, os, re, socketserver, sys

ROOT = os.path.dirname(os.path.abspath(__file__))


class RangeHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_head(self):
        rng = self.headers.get("Range")
        if not rng:
            return super().send_head()

        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().send_head()

        m = re.match(r"bytes=(\d*)-(\d*)", rng.strip())
        if not m:
            return super().send_head()

        size = os.path.getsize(path)
        start, end = m.group(1), m.group(2)
        if start == "":                      # suffix range: last N bytes
            length = int(end)
            start = max(0, size - length)
            end = size - 1
        else:
            start = int(start)
            end = int(end) if end else size - 1
        if start >= size:
            self.send_error(416, "Requested Range Not Satisfiable")
            return None
        end = min(end, size - 1)

        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        # SimpleHTTPRequestHandler copies to EOF, so hand it only the slice
        return _Slice(f, end - start + 1)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))


class _Slice:
    """File wrapper that stops after n bytes."""
    def __init__(self, f, n):
        self.f, self.left = f, n

    def read(self, amt=-1):
        if self.left <= 0:
            return b""
        if amt is None or amt < 0:
            amt = self.left
        data = self.f.read(min(amt, self.left))
        self.left -= len(data)
        return data

    def close(self):
        self.f.close()


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8130
    print(f"serving {ROOT} on http://localhost:{port}", flush=True)
    Server(("127.0.0.1", port), RangeHandler).serve_forever()
