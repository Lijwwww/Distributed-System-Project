from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
import os
from xmlrpc.client import ServerProxy
import argparse
import time

SERVER_DIR = "ServerFiles"
os.makedirs(SERVER_DIR, exist_ok=True)

class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

class SlaveServer:
    def __init__(self, host, base_port, master_url, secure_server_url, slave_id):
        port = base_port + slave_id - 1
        self.server = ThreadedXMLRPCServer((host, port))
        self.slave_url = f"http://{host}:{port}"
        self.master_url = master_url
        self.secure_server_url = secure_server_url
        self.slave_dir = os.path.join(SERVER_DIR, f'Slave_{slave_id}')
        self.slave_id = slave_id
        os.makedirs(self.slave_dir, exist_ok=True)
    
    def register_to_master(self):
        while True:
            try:
                master_proxy = ServerProxy(self.master_url)
                return master_proxy.register(self.slave_id, self.slave_url)
            except Exception as e:
                print(f"Error registering to Master: {e}")
                print("Retrying in 5 seconds...")
                time.sleep(5)
    
    def synchronize_from_master(self, file_list):
        try:
            self.clear_files()
            master_proxy = ServerProxy(self.master_url)
            for file_name in file_list:
                file_data = master_proxy.download_file(file_name)
                save_path = os.path.join(self.slave_dir, file_name)
                with open(save_path, 'w') as local_file:
                    local_file.write(file_data)
            return True

        except Exception as e:
            print(f"Error synchronizing to Master: {e}")
            return False

    def clear_files(self):
        file_list = os.listdir(self.slave_dir)

        # 遍历文件列表并删除文件
        for file_name in file_list:
            file_path = os.path.join(self.slave_dir, file_name)
            os.remove(file_path)

    def start(self):
        self.server.register_function(self.upload_file, 'upload_file')
        self.server.register_function(self.download_file, 'download_file')
        self.server.register_function(self.delete_file, 'delete_file')
        self.server.register_function(self.create_file, 'create_file')
        
        ret = self.register_to_master()
        print(f"Successfully registered Slave {self.slave_id} to Master.")
        
        if not self.synchronize_from_master(ret):
            return
        print(f"Successfully sychronize slave {self.slave_id} with Master.")

        print(f"Slave server {self.slave_id} is running, listening to port {self.server.server_address[1]}...")
        self.server.serve_forever()

    def upload_file(self, file_name, file_data):
        print(f'Uploading {file_name}...')
        file_path = os.path.join(self.slave_dir, file_name)
        # 写入文件
        with open(file_path, 'w') as file:
            file.write(file_data)
        print(f'Successfully upload {file_name}')
        return True
    
    def download_file(self, file_name):
        file_path = os.path.join(self.slave_dir, file_name)
        if not os.path.exists(file_path):
            return False
        with open(file_path, 'r') as f:
            return f.read()
        
    def delete_file(self, file_name):
        file_path = os.path.join(self.slave_dir, file_name)
        if not os.path.exists(file_path):
            return False

        print(f'Deleting {file_name}...')
        os.remove(file_path)
        print(f'Successfully delete {file_name}')

        return True
    
    def create_file(self, file_name):
        file_path = os.path.join(self.slave_dir, file_name)
        if os.path.exists(file_path):
            return False

        print(f'Creating {file_name}...')
        with open(file_path, 'w') as f:
            pass  # 创建一个空文件
        print(f'Successfully create {file_name}')

        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the Slave Server.')
    parser.add_argument('slave_id', type=int, help='The ID of the slave server.')
    parser.add_argument('--base_port', type=int, default=8891, help='The base port of the slave servers.')
    args = parser.parse_args()


    base_port = args.base_port
    master_url = 'http://localhost:8888'
    secure_server_url = 'http://localhost:8889'
    slave_id = args.slave_id

    slave_server = SlaveServer('localhost', base_port, master_url, secure_server_url, slave_id)
    slave_server.start()