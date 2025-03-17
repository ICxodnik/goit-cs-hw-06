
import http.server
import socketserver
import os
import urllib.parse
import json
from datetime import datetime

PORT = 3000
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "./static")

class WebHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
            
        # Serve static files
        file_path = os.path.join(STATIC_DIR, self.path.lstrip('/'))
        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.send_response(200)
            if file_path.endswith('.html'):
                self.send_header('Content-type', 'text/html')
            elif file_path.endswith('.css'):
                self.send_header('Content-type', 'text/css')
            elif file_path.endswith('.js'):
                self.send_header('Content-type', 'application/javascript')
            elif file_path.endswith('.png'):
                self.send_header('Content-type', 'image/png')
            self.end_headers()
            
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    

def run_server():
    with socketserver.TCPServer(("", PORT), WebHandler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
