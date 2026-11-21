#!/usr/bin/env python3
"""Optional LAN-only bridge for Wholphin REC -> NAS IPTV update script.

Provides a narrowly scoped POST webhook with a high-entropy secret in the URL.
No arbitrary shell command, no dynamic script parameter, no Jellyfin token.
"""
from __future__ import annotations

import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread

HOST = os.environ.get("WHOL_REC_BIND", "127.0.0.1")
PORT = int(os.environ.get("WHOL_REC_PORT", "8767"))
TOKEN = os.environ.get("WHOL_REC_TOKEN", "")
IPTV_SCRIPT = Path(os.environ.get("WHOL_REC_IPTV_SCRIPT", ""))
TIMEOUT = int(os.environ.get("WHOL_REC_TIMEOUT", "180"))

if len(TOKEN) < 32:
    sys.exit("Set WHOL_REC_TOKEN to a random secret of at least 32 characters")
if not IPTV_SCRIPT.is_file() or IPTV_SCRIPT.suffix != ".py":
    sys.exit("Set WHOL_REC_IPTV_SCRIPT to the existing absolute Python updater path")
if TIMEOUT < 30 or TIMEOUT > 3600:
    sys.exit("WHOL_REC_TIMEOUT must be between 30 and 3600 seconds")

mutex = Lock()
status_lock = Lock()
status: dict[str, str] = {"state": "idle", "last_result": "not started"}


def run_iptv() -> None:
    with status_lock:
        status["state"] = "running"
        status["last_result"] = "started"
    try:
        result = subprocess.run(
            [sys.executable, str(IPTV_SCRIPT.resolve())],
            cwd=IPTV_SCRIPT.parent,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            check=False,
        )
        with status_lock:
            status["state"] = "idle"
            status["last_result"] = "success" if result.returncode == 0 else f"exit={result.returncode}"
        print("IPTV updater:", status["last_result"], (result.stderr or "")[-500:])
    except Exception as exc:
        with status_lock:
            status["state"] = "idle"
            status["last_result"] = type(exc).__name__
        print("IPTV updater failed:", type(exc).__name__)
    finally:
        mutex.release()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Avoid logging the secret embedded in the webhook URI.
        print("Whol REC bridge:", self.client_address[0], self.command, self.path.split("/hooks/")[0] or "/hooks/[redacted]")

    def reply(self, status_code: int, payload: dict[str, str]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        parts = self.path.split("?")[0].split("/")
        return (
            len(parts) == 4
            and parts[0] == ""
            and parts[1] == "hooks"
            and parts[2] == "iptv"
            and hmac.compare_digest(parts[3], TOKEN)
        )

    def do_GET(self):
        if self.path == "/health":
            self.reply(200, {"service": "whol-rec-iptv", "state": "ready"})
        elif self.authorized():
            with status_lock:
                self.reply(200, status.copy())
        else:
            self.reply(404, {"error": "not found"})

    def do_POST(self):
        if not self.authorized():
            self.reply(404, {"error": "not found"})
            return
        if not mutex.acquire(blocking=False):
            self.reply(409, {"error": "already running"})
            return
        Thread(target=run_iptv, daemon=True).start()
        self.reply(202, {"status": "accepted"})


if __name__ == "__main__":
    print(f"Whol REC NAS IPTV bridge listening at {HOST}:{PORT} (secret redacted)")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
