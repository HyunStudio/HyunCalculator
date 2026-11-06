"""Local desktop web UI. Requests stay on the loopback interface."""
from __future__ import annotations
import json
import math
import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import numpy as np
from .operations import GROUPS
from .scientific import calculate
from .graphing import sample_curves
from .codegen import generate, GenerationOptions, bundle_bytes

ASSETS=Path(__file__).with_name('webui')

def serializable(value):
    if isinstance(value,dict):return {str(k):serializable(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,np.ndarray)):return [serializable(v) for v in value]
    if isinstance(value,(int,np.integer)) and not isinstance(value,bool):return str(value) if abs(value)>2**53-1 else int(value)
    if isinstance(value,(float,np.floating)):return float(value) if math.isfinite(value) else None
    if isinstance(value,complex):return str(value)
    return value

def compute(payload):
    mode=payload.get('mode')
    if mode=='scientific':return calculate(str(payload['expression']),degrees=payload.get('degrees',False))
    if mode=='graph':return [{'label':label,'x':serializable(x),'y':serializable(y)} for label,x,y in sample_curves(str(payload['expression']),float(payload.get('min',-10)),float(payload.get('max',10)),501)]
    if mode=='codegen':
        opts=GenerationOptions(**payload.get('options',{}))
        return generate(payload['formula'],opts)
    operations={op.compute.__name__:op for ops in GROUPS.values() for op in ops}
    operation=operations.get(payload.get('operation'))
    if operation is None:raise ValueError('Unknown calculation')
    fields=payload.get('fields',{})
    if not isinstance(fields,dict) or any(not isinstance(v,str) or len(v)>20000 for v in fields.values()):raise ValueError('Invalid input fields')
    return operation.compute(fields)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ASSETS),**kwargs)
    def log_message(self,*args):pass
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        super().end_headers()
    def do_GET(self):
        if self.path.split('?')[0]=='/api/status':
            body=b'{"engine":"python"}'
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
        super().do_GET()
    def do_POST(self):
        if self.path!='/api/compute':self.send_error(404);return
        # Browser requests must originate from the local UI itself.
        origin=self.headers.get('Origin')
        if origin and origin!=f'http://{self.headers.get("Host")}':self.send_error(403);return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=131072:raise ValueError('Input is too large')
            data=json.loads(self.rfile.read(size))
            result={'result':serializable(compute(data))}
            status=200
        except (ValueError,KeyError,TypeError,OverflowError,ZeroDivisionError, np.linalg.LinAlgError) as exc:
            result={'error':str(exc)};status=400
        body=json.dumps(result,ensure_ascii=False,allow_nan=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)

def run_modern(lang='ko',browser=False):
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    url=f'http://127.0.0.1:{server.server_port}/?lang={lang}'
    try:
        if not browser:
            try:
                import webview
            except ImportError:pass
            else:
                try:
                    webview.create_window('HyunCalculator',url,width=1440,height=950,min_size=(900,650),background_color='#1E1F22')
                    webview.start();return
                except Exception as exc:
                    print(f'Native window unavailable; opening browser: {exc}')
        webbrowser.open(url)
        thread.join()
    except KeyboardInterrupt:pass
    finally:server.shutdown();server.server_close()
