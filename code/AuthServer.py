from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
import os
from xmlrpc.client import ServerProxy
import argparse
import time
import threading

SERVER_DIR = "ServerFiles"
os.makedirs(SERVER_DIR, exist_ok=True)

class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

class AuthenticateServer:
    def __init__(self, host, port, master_url):
        self.server = ThreadedXMLRPCServer((host, port))
        self.server_url = f"http://{host}:{port}"
        self.master_url = master_url
        self.server_dir = os.path.join(SERVER_DIR, "Authenticate")
        self.auth_lock = threading.Lock()
        self.auth_list = {}
        os.makedirs(self.server_dir, exist_ok=True)

        auth = os.path.join(self.server_dir, 'auth.txt')
        if not os.path.exists(auth):
            with open(auth, 'w'):
                pass 
        with open(os.path.join(self.server_dir, 'auth.txt'), 'r') as f:
            lines = f.readlines()
            for line in lines:
                username, password = line.split()
                self.auth_list[username] = password
            print(f'Users registered: {self.auth_list}')

    def start(self):
        self.server.register_function(self.login, 'login')
        self.server.register_function(self.signup, 'signup')

        print(f"Authenticate server is running, listening to port {self.server.server_address[1]}...")
        self.server.serve_forever()
    
    def login(self, username, password):
        if username not in self.auth_list:
            return False
        elif self.auth_list[username] != password:
            return False
        else:
            return self.master_url

    def signup(self, username, password):
        if username in self.auth_list:
            return False
        
        self.auth_list[username] = [password]
        with self.auth_lock, open(os.path.join(self.server_dir, 'auth.txt'), 'a+') as f:
            f.write(f'{username} {password}\n')
        print(f'Signup: {username} {password}')
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the Slave Server.')
    parser.add_argument('--port', type=int, default=8890, help='The port of the AuthenticateServer.')
    args = parser.parse_args()

    port = args.port
    master_url = 'http://localhost:8888'

    auth_server = AuthenticateServer('localhost', port, master_url)
    auth_server.start()