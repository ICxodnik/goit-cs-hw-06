import http.server
import multiprocessing
import socket
import socketserver
import os
import urllib.parse
import json
from datetime import datetime
import socket
import logging

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
            self.wfile.flush()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open(os.path.join(STATIC_DIR, 'error.html'), 'rb') as f:
                self.wfile.write(f.read())
            self.wfile.flush()
            
    def do_POST(self):
        if self.path != '/message':
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open(os.path.join(STATIC_DIR, 'error.html'), 'rb') as f:
                self.wfile.write(f.read())
            self.wfile.flush()
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
            self.wfile.flush()
            return
        
        try:
            json_data = json.dumps({
                'username': username,
                'message': message,
                'date': datetime.now().isoformat()
            })
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(json_data.encode('utf-8'), (SOCKET_HOST, SOCKET_PORT))
            logging.info(f'Data sent to server: {json_data}')
                
        except Exception as e:
            logging.error(f'Error processing POST request: {e}')
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes("Internal Server Error: " + str(e), 'utf-8'))
            self.wfile.flush()
            return
        
        # Redirect back to the form
        self.send_response(303)  # See Other
        self.send_header('Location', '/message.html')
        self.end_headers()
        self.wfile.write(b'')
        self.wfile.flush()

def run_server():
    with socketserver.TCPServer(("", PORT), WebHandler) as httpd:
        logging.info(f"Server started at http://localhost:{PORT}")
        httpd.serve_forever()

def start_socket_server():
    client = MongoClient(MONGO_URI)
    db = client.simple_app
        
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', 5000))
    
    while True:
        data, _ = sock.recvfrom(1024 * 10)
        
        record = json.loads(data.decode('utf-8'))
        logging.info(f"Data received: {record}")
        
        try:
            result = db.messages.insert_one(record)
            logging.info(f"Data saved to MongoDB: {result.inserted_id}")
        except Exception as e:
            logging.error(f'Error: {e}')

            
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="[%(asctime)s] %(message)s",
        datefmt="%d/%b/%Y %H:%M:%S"
    )
    
    logging.info("Starting socket server")
    
    socket_server = multiprocessing.Process(
        target=start_socket_server,
        args=(),
    )
    socket_server.start()
    
    # don't need to run in separate process as we already have initial
    run_server()
