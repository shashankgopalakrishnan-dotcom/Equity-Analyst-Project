"""Local browser interface for the equity desk."""
from __future__ import annotations

import base64
import hmac
import json
import math
import os
import re
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

PROJECT = Path(__file__).resolve().parents[2]
WORKSPACE = PROJECT.parent.parent
RUNS = PROJECT.parent / "lab4_runs"
load_dotenv(WORKSPACE / ".env")
ACCESS_USERNAME = "classmate"
ACCESS_PASSWORD = os.environ.get("LAB5_UI_PASSWORD", "")
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()

PAGE = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Equity research desk</title>
  <style>
    body { font: 16px sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }
    label { display: block; margin: 1rem 0; }
    input { padding: .5rem; }
    pre { white-space: pre-wrap; background: #f3f3f3; padding: 1rem; }
    button { padding: .6rem 1.3rem; }
    button:disabled { opacity: .6; }
  </style>
</head>
<body>
  <h1>Equity research desk</h1>
  <form id="form">
    <label>Ticker <input name="ticker" required></label>
    <label>Peers, separated by commas <input name="peers"></label>
    <label>Price <input name="price" type="number" min="0.01" step="any" required></label>
    <button>Run</button>
  </form>
  <h2>Progress</h2>
  <pre id="progress"></pre>
  <h2>Verified report</h2>
  <pre id="report"></pre>
  <script>
    document.querySelector('#form').onsubmit = async (event) => {
      event.preventDefault();
      const button = event.target.querySelector('button');
      const progress = document.querySelector('#progress');
      const report = document.querySelector('#report');
      button.disabled = true;
      progress.textContent = 'Starting…\\n';
      report.textContent = '';

      try {
        const response = await fetch('/run', {
          method: 'POST',
          body: new URLSearchParams(new FormData(event.target))
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || `Run request failed (${response.status}).`);

        let cursor = 0;
        const poll = async () => {
          try {
            const statusResponse = await fetch(
              `/status?id=${encodeURIComponent(data.id)}&cursor=${cursor}`,
              { cache: 'no-store' }
            );
            if (!statusResponse.ok) throw new Error(`Status request failed (${statusResponse.status}).`);
            const status = await statusResponse.json();
            let finished = false;
            for (const message of status.events) {
              if (message.kind === 'log') progress.textContent += message.text + '\\n';
              if (message.kind === 'report') report.textContent = message.text;
              if (message.kind === 'done') {
                progress.textContent += `Finished (exit code ${message.code}).`;
                finished = true;
              }
            }
            cursor = status.cursor;
            if (finished || status.done) {
              button.disabled = false;
              return;
            }
            window.setTimeout(poll, 500);
          } catch (error) {
            progress.textContent += `\\n${String(error)}`;
            button.disabled = false;
          }
        };
        poll();
      } catch (error) {
        progress.textContent = String(error);
        button.disabled = false;
      }
    };
  </script>
</body>
</html>
"""


def publish(job: str, message: dict) -> None:
    with jobs_lock:
        state = jobs.get(job)
        if state is None:
            return
        state["events"].append(message)
        if message.get("kind") == "done":
            state["done"] = True


def launch(job: str, ticker: str, peers: str, price: str) -> None:
    command = [sys.executable, "-u", "-m", "week3_process_demo.lab4_flow", ticker]
    if peers:
        command += ["--peers", peers]
    if price:
        command += ["--price", price]

    try:
        process = subprocess.Popen(
            command,
            cwd=PROJECT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        output: list[str] = []
        assert process.stdout is not None
        for line in process.stdout:
            clean_line = line.rstrip()
            output.append(clean_line)
            publish(job, {"kind": "log", "text": clean_line})

        code = process.wait()
        for line in reversed(output):
            candidate = Path(line.removeprefix("Verified report: ").strip()).expanduser()
            if candidate.suffix == ".md" and candidate.is_file():
                resolved = candidate.resolve()
                if resolved.is_relative_to(RUNS.resolve()) and "_verified_report" in resolved.name:
                    publish(job, {"kind": "report", "text": resolved.read_text(encoding="utf-8")})
                    break
        publish(job, {"kind": "done", "code": code})
    except Exception as error:
        publish(job, {"kind": "log", "text": str(error)})
        publish(job, {"kind": "done", "code": 1})


class Handler(BaseHTTPRequestHandler):
    def _authorized(self) -> bool:
        if not ACCESS_PASSWORD:
            return True
        expected_value = f"{ACCESS_USERNAME}:{ACCESS_PASSWORD}".encode("utf-8")
        expected = "Basic " + base64.b64encode(expected_value).decode("ascii")
        actual = self.headers.get("Authorization", "")
        if actual and hmac.compare_digest(actual, expected):
            return True
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Equity Research Desk"')
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    def _json(self, status_code: int, data: dict) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if not self._authorized():
            return
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/status":
            query = parse_qs(parsed.query)
            job = query.get("id", [""])[0]
            try:
                cursor = max(0, int(query.get("cursor", ["0"])[0]))
            except ValueError:
                self._json(400, {"error": "Cursor must be an integer."})
                return
            with jobs_lock:
                state = jobs.get(job)
                if state is None:
                    self._json(404, {"error": "Run not found."})
                    return
                events = state["events"]
                payload = {
                    "events": events[cursor:],
                    "cursor": len(events),
                    "done": state["done"],
                }
            self._json(200, payload)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if not self._authorized():
            return
        if self.path != "/run":
            self.send_error(404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size > 4096:
                raise ValueError("Request too large.")
            form = parse_qs(self.rfile.read(size).decode("utf-8"))
            ticker = form.get("ticker", [""])[0].strip().upper()
            peers = form.get("peers", [""])[0].strip().upper()
            price = form.get("price", [""])[0].strip()

            if not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", ticker):
                raise ValueError("Enter a valid ticker.")
            if peers and not re.fullmatch(r"[A-Z0-9., -]+", peers):
                raise ValueError("Enter valid peers.")
            if not price:
                raise ValueError("Enter a price.")
            if not math.isfinite(float(price)) or float(price) <= 0:
                raise ValueError("Price must be a positive number.")

            job = uuid.uuid4().hex
            with jobs_lock:
                jobs[job] = {"events": [], "done": False}
            threading.Thread(target=launch, args=(job, ticker, peers, price), daemon=True).start()
            self._json(200, {"id": job})
        except ValueError as error:
            self._json(400, {"error": str(error)})


if __name__ == "__main__":
    if not ACCESS_PASSWORD:
        print("LAB5_UI_PASSWORD is not set; the page is available only on this laptop.", flush=True)
    print("Open http://127.0.0.1:8765", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
