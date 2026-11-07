"""Local browser interface for the equity desk."""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Queue
from urllib.parse import parse_qs, urlparse

PROJECT = Path(__file__).resolve().parents[2]
RUNS = PROJECT.parent / 'lab4_runs'
jobs = {}
PAGE = '''<!doctype html><html><head><meta charset="utf-8"><title>Equity research desk</title><style>body{font:16px sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem}label{display:block;margin:1rem 0}input{padding:.5rem}pre{white-space:pre-wrap;background:#f3f3f3;padding:1rem}button{padding:.6rem 1.3rem}button:disabled{opacity:.6}</style></head><body><h1>Equity research desk</h1><form id="form"><label>Ticker <input name="ticker" required></label><label>Peers, separated by commas <input name="peers"></label><label>Price <input name="price" type="number" min="0.01" step="any"></label><button>Run</button></form><h2>Progress</h2><pre id="progress"></pre><h2>Verified report</h2><pre id="report"></pre><script>document.querySelector('#form').onsubmit=async e=>{e.preventDefault();let b=e.target.querySelector('button'),p=document.querySelector('#progress'),r=document.querySelector('#report');b.disabled=true;p.textContent='Starting…\\n';r.textContent='';try{let res=await fetch('/run',{method:'POST',body:new URLSearchParams(new FormData(e.target))});let data=await res.json();if(!res.ok){p.textContent=data.error;b.disabled=false;return}let s=new EventSource('/events?id='+data.id);s.onmessage=e=>{let m=JSON.parse(e.data);if(m.kind==='log')p.textContent+=m.text+'\\n';if(m.kind==='report')r.textContent=m.text;if(m.kind==='done'){p.textContent+='Finished (exit code '+m.code+').';s.close();b.disabled=false}};s.onerror=()=>{p.textContent+='Connection ended.';s.close();b.disabled=false}}catch(err){p.textContent=String(err);b.disabled=false}};</script></body></html>'''

def launch(job, ticker, peers, price):
    q = jobs[job]
    command = [sys.executable, '-u', '-m', 'week3_process_demo.lab4_flow', ticker]
    if peers: command += ['--peers', peers]
    if price: command += ['--price', price]
    try:
        proc = subprocess.Popen(command, cwd=PROJECT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        output = []
        for line in proc.stdout:
            output.append(line.rstrip())
            q.put({'kind': 'log', 'text': line.rstrip()})
        code = proc.wait()
        for line in reversed(output):
            candidate = Path(line.removeprefix('Verified report: ').strip()).expanduser()
            if candidate.suffix == '.md' and candidate.is_file():
                resolved = candidate.resolve()
                if resolved.is_relative_to(RUNS.resolve()) and '_verified_report' in resolved.name:
                    q.put({'kind': 'report', 'text': resolved.read_text(encoding='utf-8')})
                    break
        q.put({'kind': 'done', 'code': code})
    except Exception as exc:
        q.put({'kind': 'log', 'text': str(exc)})
        q.put({'kind': 'done', 'code': 1})

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/':
            body = PAGE.encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
        if parsed.path == '/events':
            job = parse_qs(parsed.query).get('id',[''])[0]
            if job not in jobs: self.send_error(404); return
            self.send_response(200); self.send_header('Content-Type','text/event-stream'); self.send_header('Cache-Control','no-cache'); self.end_headers()
            while True:
                message = jobs[job].get()
                try: self.wfile.write(('data: '+json.dumps(message)+'\n\n').encode()); self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError): break
                if message['kind'] == 'done': break
            return
        self.send_error(404)

    def do_POST(self):
        if self.path != '/run': self.send_error(404); return
        try:
            size = int(self.headers.get('Content-Length','0'))
            if size > 4096: raise ValueError('Request too large')
            form = parse_qs(self.rfile.read(size).decode())
            ticker = form.get('ticker',[''])[0].strip().upper()
            peers = form.get('peers',[''])[0].strip().upper()
            price = form.get('price',[''])[0].strip()
            if not re.fullmatch(r'[A-Z][A-Z0-9.-]{0,9}',ticker): raise ValueError('Enter a valid ticker.')
            if peers and not re.fullmatch(r'[A-Z0-9., -]+',peers): raise ValueError('Enter valid peers.')
            if price and (not float(price) > 0): raise ValueError('Price must be positive.')
            job = uuid.uuid4().hex; jobs[job] = Queue()
            threading.Thread(target=launch,args=(job,ticker,peers,price),daemon=True).start()
            body = json.dumps({'id':job}).encode(); self.send_response(200)
        except ValueError as exc:
            body = json.dumps({'error':str(exc)}).encode(); self.send_response(400)
        self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)

if __name__ == '__main__':
    print('Open http://127.0.0.1:8765', flush=True)
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
