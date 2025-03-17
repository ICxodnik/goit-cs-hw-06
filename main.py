import http.server
import multiprocessing
import socket
import socketserver
import os
import urllib.parse
import json
from datetime import datetime
import socket

from pymongo import MongoClient

PORT = 3000
SOCKET_HOST = 'localhost'
SOCKET_PORT = 5000
MONGO_URI = "mongodb://mongo:27017"
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
            with open(os.path.join(STATIC_DIR, 'error.html'), 'rb') as f:
                self.wfile.write(f.read())
    
    def do_POST(self):
        if self.path != '/message':
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open(os.path.join(STATIC_DIR, 'error.html'), 'rb') as f:
                self.wfile.write(f.read())
            return
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        form_data = urllib.parse.parse_qs(post_data)
            
        username = form_data.get('username', [''])[0]
        message = form_data.get('message', [''])[0]
        
        if not (username and message):
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Bad Request: Username and message are required')
            return
        
        try:
            json_data = json.dumps({
                'username': username,
                'message': message,
                'date': datetime.now().isoformat()
            })
            with socket.socket() as s:
                s.connect((SOCKET_HOST, SOCKET_PORT))
                s.sendall(json_data.encode('utf-8'))
                print(f'Data sent to server: {json_data}')
                
        except Exception as e:
            print(f'Error: {e}')
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Internal Server Error')
            return
        
        # Redirect back to the form
        self.send_response(303)  # See Other
        self.send_header('Location', '/message.html')
        self.end_headers()

def run_server():
    with socketserver.TCPServer(("", PORT), WebHandler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        httpd.serve_forever()

def start_socket_server():
    client = MongoClient(MONGO_URI)
    db = client.simple_app
        
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', 5000))
    sock.listen(1)
    conn, addr = sock.accept()

    while True:
        data = conn.recv(1024 * 10)
        if not data:
            break
        
        record = json.loads(data.decode('utf-8'))
        print("Data received", record)
        
        try:
            result = db.messages.insert_one(record)
            print("Data saved to MongoDB", result.inserted_id)
        except Exception as e:
            print(f'Error: {e}')
        

    conn.close()

            
if __name__ == "__main__":
    
    socket_server = multiprocessing.Process(
        target=start_socket_server,
        args=(),
    )
    socket_server.start()
    
    # don't need to run in separate process as we already have initial
    run_server()
