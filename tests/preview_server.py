"""Serve a checkout with a real 404 response, at root or a project prefix."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--port',type=int,default=8781)
parser.add_argument('--prefix',default='')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
prefix=args.prefix.rstrip('/')

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*values,**kwargs):super().__init__(*values,directory=str(root),**kwargs)
    def translate_path(self,path):
        if prefix and path.startswith(prefix+'/'):path=path[len(prefix):]
        return super().translate_path(path)
    def send_error(self,code,message=None,explain=None):
        if code==404:
            body=(root/'404.html').read_bytes()
            self.send_response(404);self.send_header('Content-Type','text/html; charset=utf-8')
            self.end_headers();self.wfile.write(body)
        else:super().send_error(code,message,explain)
    def log_message(self,*values):pass

ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
