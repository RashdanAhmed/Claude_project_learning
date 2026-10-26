#!/usr/bin/env python3
"""GRC Task Desk: runs the task desk as a web app on this computer.

Needs Python 3.8 or later and nothing else. Tasks, projects and routines are kept
in a SQLite database and pictures as files, all inside one data folder.

    python3 server.py              serve http://localhost:8765/
    python3 server.py --open       ...and open it in your browser
    python3 server.py --help       list every option
"""

import argparse
import json
import os
import re
import secrets
import shutil
import socket
import sqlite3
import sys
import tempfile
import threading
import time
import webbrowser
import zipfile
from datetime import date, datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

if sys.version_info < (3, 8):
    sys.exit("GRC Task Desk needs Python 3.8 or later. Download it from https://www.python.org/downloads/")

APP_DIR = Path(__file__).resolve().parent
INDEX = APP_DIR / "static" / "index.html"
COLLECTIONS = ("tasks", "projects", "routines")
ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MAX_JSON_BYTES = 1024 * 1024
MAX_PICTURE_BYTES = 20 * 1024 * 1024
# A picture is uploaded before its task is saved, so only sweep unreferenced ones once they are old.
ORPHAN_GRACE_SECONDS = 24 * 3600
LOOPBACK = {"127.0.0.1", "localhost", "::1"}
PICTURE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
CSP = (
    "default-src 'self'; script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
    "img-src 'self' blob: data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
)


def sniff_picture(data):
    """Returns the file extension for a supported picture, judged by its bytes rather than its name."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


class Store:
    """Tasks, projects and routines as JSON documents in SQLite, pictures as files beside the database."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.pictures = data_dir / "pictures"
        self.pictures.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.db = sqlite3.connect(str(data_dir / "grc-task-desk.db"), check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        with self.db:
            for coll in COLLECTIONS:
                self.db.execute(
                    f"CREATE TABLE IF NOT EXISTS {coll} (id TEXT PRIMARY KEY, body TEXT NOT NULL, updated_at TEXT NOT NULL)"
                )
        # Pages compare revisions for equality only, so a fresh starting value per run is enough.
        self.revision = int(time.time() * 1000)

    def close(self):
        with self.lock:
            self.db.close()

    def state(self):
        with self.lock:
            out = {"revision": self.revision}
            for coll in COLLECTIONS:
                rows = self.db.execute(f"SELECT id, body FROM {coll}").fetchall()
                out[coll] = [{**json.loads(body), "id": doc_id} for doc_id, body in rows]
            return out

    def put(self, coll, doc_id, body):
        body.pop("id", None)
        stamp = datetime.now(timezone.utc).isoformat()
        with self.lock, self.db:
            self.db.execute(
                f"INSERT OR REPLACE INTO {coll} (id, body, updated_at) VALUES (?, ?, ?)",
                (doc_id, json.dumps(body, ensure_ascii=False), stamp),
            )
            self.revision += 1
            return self.revision

    def delete(self, coll, doc_id):
        with self.lock, self.db:
            self.db.execute(f"DELETE FROM {coll} WHERE id = ?", (doc_id,))
            self.revision += 1
            return self.revision

    def save_picture(self, data):
        ext = sniff_picture(data)
        if not ext:
            return None
        pic_id = secrets.token_hex(16)
        path = self.pictures / (pic_id + ext)
        part = self.pictures / (pic_id + ext + ".part")
        part.write_bytes(data)
        os.replace(part, path)
        return pic_id

    def picture_path(self, pic_id):
        for ext in PICTURE_TYPES:
            path = self.pictures / (pic_id + ext)
            if path.is_file():
                return path
        return None

    def delete_picture(self, pic_id):
        path = self.picture_path(pic_id)
        if path:
            path.unlink()

    def sweep_orphans(self):
        """Deletes day-old pictures that no task points at, such as ones added to a task that was never saved."""
        referenced = set()
        for task in self.state()["tasks"]:
            images = task.get("images")
            if isinstance(images, list):
                referenced.update(i for i in images if isinstance(i, str))
        cutoff = time.time() - ORPHAN_GRACE_SECONDS
        removed = 0
        for path in self.pictures.iterdir():
            if path.suffix in PICTURE_TYPES and path.stem not in referenced and path.stat().st_mtime < cutoff:
                path.unlink()
                removed += 1
        return removed

    def write_backup(self, out):
        """Writes a zip laid out like the data folder: the database plus a pictures folder."""
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "grc-task-desk.db"
            dest = sqlite3.connect(str(snapshot))
            with self.lock:
                self.db.backup(dest)
            dest.close()
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
                z.write(snapshot, "grc-task-desk.db")
                for path in sorted(self.pictures.iterdir()):
                    if path.suffix in PICTURE_TYPES:
                        z.write(path, "pictures/" + path.name, compress_type=zipfile.ZIP_STORED)


class Handler(BaseHTTPRequestHandler):
    server_version = "GRCTaskDesk/1.0"
    sys_version = ""

    def log_message(self, fmt, *args):
        if self.server.verbose:
            super().log_message(fmt, *args)

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def do_PUT(self):
        self.dispatch("PUT")

    def do_DELETE(self):
        self.dispatch("DELETE")

    def dispatch(self, method):
        try:
            if not self.host_allowed():
                return self.send_json({"error": "This address isn't allowed."}, HTTPStatus.FORBIDDEN)
            if method != "GET" and not self.same_origin():
                return self.send_json({"error": "Requests from other sites aren't allowed."}, HTTPStatus.FORBIDDEN)
            path = urlsplit(self.path).path
            if method == "GET" and path in ("/", "/index.html"):
                return self.send_index()
            parts = path.strip("/").split("/")
            if parts[0] == "api":
                return self.route_api(method, parts[1:])
            return self.send_json({"error": "Not found."}, HTTPStatus.NOT_FOUND)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:  # keep serving; report the failure to the page
            print(f"Error handling {method} {self.path}: {e!r}", file=sys.stderr)
            try:
                self.send_json({"error": "Something went wrong on the server."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            except OSError:
                pass

    def route_api(self, method, route):
        store = self.server.store
        if route == ["state"] and method == "GET":
            return self.send_json(store.state())
        if route == ["revision"] and method == "GET":
            return self.send_json({"revision": store.revision})
        if route == ["backup"] and method == "GET":
            return self.send_backup()
        if route == ["pictures"] and method == "POST":
            return self.upload_picture()
        if len(route) == 2 and ID_RE.match(route[1]):
            kind, doc_id = route
            if kind == "pictures" and method == "GET":
                return self.send_picture(doc_id)
            if kind == "pictures" and method == "DELETE":
                store.delete_picture(doc_id)
                return self.send_empty()
            if kind in COLLECTIONS and method == "PUT":
                body = self.read_json()
                if body is not None:
                    self.send_json({"revision": store.put(kind, doc_id, body)})
                return None
            if kind in COLLECTIONS and method == "DELETE":
                return self.send_json({"revision": store.delete(kind, doc_id)})
        return self.send_json({"error": "Not found."}, HTTPStatus.NOT_FOUND)

    # Request checks. Bound to this computer, the app only answers to its own names, which stops
    # other websites reaching it through DNS tricks; writes must come from the app's own page.
    def host_allowed(self):
        if self.server.any_host:
            return True
        host = self.headers.get("Host", "")
        name = host[1:host.find("]")] if host.startswith("[") else host.split(":")[0]
        return name.lower() in LOOPBACK

    def same_origin(self):
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        return urlsplit(origin).netloc.lower() == self.headers.get("Host", "").lower()

    def read_body(self, limit):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0:
            self.close_connection = True
            self.send_json({"error": "Missing or invalid Content-Length."}, HTTPStatus.LENGTH_REQUIRED)
            return None
        if length > limit:
            self.close_connection = True
            self.send_json({"error": "That's too large."}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return None
        return self.rfile.read(length)

    def read_json(self):
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            self.close_connection = True
            self.send_json({"error": "Send JSON."}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
            return None
        raw = self.read_body(MAX_JSON_BYTES)
        if raw is None:
            return None
        try:
            body = json.loads(raw)
        except ValueError:
            body = None
        if not isinstance(body, dict):
            self.send_json({"error": "Send a JSON object."}, HTTPStatus.BAD_REQUEST)
            return None
        return body

    # Responses
    def send_common(self, status, content_type, length):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")

    def send_json(self, data, status=HTTPStatus.OK):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_common(status, "application/json; charset=utf-8", len(body))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_empty(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def send_index(self):
        body = INDEX.read_bytes()
        self.send_common(HTTPStatus.OK, "text/html; charset=utf-8", len(body))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Security-Policy", CSP)
        self.end_headers()
        self.wfile.write(body)

    def upload_picture(self):
        if not self.headers.get("Content-Type", "").startswith("image/"):
            self.close_connection = True
            return self.send_json({"error": "Send a PNG, JPEG, GIF or WebP picture."}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        data = self.read_body(MAX_PICTURE_BYTES)
        if data is None:
            return None
        pic_id = self.server.store.save_picture(data)
        if not pic_id:
            return self.send_json({"error": "Send a PNG, JPEG, GIF or WebP picture."}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        return self.send_json({"id": pic_id}, HTTPStatus.CREATED)

    def send_picture(self, pic_id):
        path = self.server.store.picture_path(pic_id)
        if not path:
            return self.send_json({"error": "Picture not found."}, HTTPStatus.NOT_FOUND)
        self.send_common(HTTPStatus.OK, PICTURE_TYPES[path.suffix], path.stat().st_size)
        self.send_header("Cache-Control", "private, max-age=31536000, immutable")
        self.end_headers()
        with path.open("rb") as f:
            shutil.copyfileobj(f, self.wfile)

    def send_backup(self):
        with tempfile.TemporaryFile() as out:
            self.server.store.write_backup(out)
            size = out.tell()
            out.seek(0)
            self.send_common(HTTPStatus.OK, "application/zip", size)
            self.send_header("Content-Disposition", f'attachment; filename="grc-task-desk-backup-{date.today().isoformat()}.zip"')
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            shutil.copyfileobj(out, self.wfile)


def lan_address():
    """This computer's address on the local network, found without sending anything."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return None


def main():
    parser = argparse.ArgumentParser(description="Run GRC Task Desk on this computer.")
    parser.add_argument("--port", type=int, default=8765, help="port to listen on (default: 8765)")
    parser.add_argument(
        "--host", default="127.0.0.1",
        help="address to listen on. The default keeps the app private to this computer. "
             "0.0.0.0 lets other computers on your network open it, with no sign-in.",
    )
    parser.add_argument("--data", type=Path, default=APP_DIR / "data",
                        help="folder for the database and pictures (default: the data folder next to this file)")
    parser.add_argument("--open", action="store_true", help="open the app in your web browser once it starts")
    parser.add_argument("--verbose", action="store_true", help="log every request")
    args = parser.parse_args()

    if not INDEX.is_file():
        sys.exit(f"Can't find {INDEX}. Keep server.py next to the static folder it came with.")
    store = Store(args.data.resolve())
    swept = store.sweep_orphans()
    try:
        server = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as e:
        store.close()
        sys.exit(f"Couldn't start on port {args.port} ({e.strerror}). Another program may be using it.\n"
                 f"Try another port, for example: python3 server.py --port {args.port + 1}")
    server.store = store
    server.any_host = args.host not in LOOPBACK
    server.verbose = args.verbose

    url = f"http://localhost:{args.port}/"
    print(f"GRC Task Desk is running at {url}")
    if server.any_host:
        print(f"Other computers on your network can open http://{lan_address() or '<this computer IP address>'}:{args.port}/")
        print("There is no sign-in: anyone who can reach this computer on that port can read and change your tasks.")
    print(f"Data folder: {store.data_dir}")
    if swept:
        print(f"Removed {swept} unused picture{'' if swept == 1 else 's'}.")
    print("Keep this window open while you use the app. Press Ctrl+C to stop it.")
    if args.open:
        threading.Timer(0.5, webbrowser.open, [url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
        store.close()


if __name__ == "__main__":
    main()
