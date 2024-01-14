from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
import os
import threading
from xmlrpc.client import ServerProxy
import copy
import argparse

SERVER_DIR = "ServerFiles"
os.makedirs(SERVER_DIR, exist_ok=True)

class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

class MasterServer:
    def __init__(self, host, port):
        self.server = ThreadedXMLRPCServer((host, port))
        self.dir_lock = threading.Lock()
        self.master_url = f"http://{host}:{port}"
        self.slave_urls = []
        self.secure_server_url = f"http://{host}:8889"
        self.master_dir = os.path.join(SERVER_DIR, "Master")
        os.makedirs(self.master_dir, exist_ok=True)

        directory = os.path.join(self.master_dir, 'directory.txt')
        if not os.path.exists(directory):
            with open(directory, 'w'):
                pass 
        with open(os.path.join(self.master_dir, 'directory.txt'), 'r') as f:
            lines = f.readlines()
            self.file_directory = [line.strip() for line in lines]
            print(f'Files on server: {", ".join(self.file_directory)}')

    def start(self):
        self.server.register_function(self.register_slave, 'register')
        self.server.register_function(self.list_files, 'list_files')
        self.server.register_function(self.request_download_file, 'request_download_file')
        self.server.register_function(self.download_file, 'download_file')
        self.server.register_function(self.upload_file, 'upload_file')
        self.server.register_function(self.create_file, 'create_file')
        self.server.register_function(self.delete_file, 'delete_file')
        print(f"Master server is running, listening to port {self.server.server_address[1]}...")
        self.server.serve_forever()

    def register_slave(self, slave_id, slave_url):
        if slave_url not in self.slave_urls:
            self.slave_urls.append(slave_url)
        print(f"Slave {slave_id} registered successfully: {slave_url}")
        return self.file_directory

    def list_files(self):
        return self.file_directory

    def request_download_file(self, file_name):
        # 文件名不存在
        if file_name not in self.file_directory:
            return False
        
        # 返回所有服务器和锁服务器的url
        server_urls = copy.copy(self.slave_urls)
        server_urls.insert(0, self.master_url)
        return (server_urls, self.secure_server_url)

    def download_file(self, file_name):
        file_path = os.path.join(self.master_dir, file_name)
        if not os.path.exists(file_path):
            return False
        with open(file_path, 'r') as f:
            return f.read()
        
    def upload_file(self, file_name, file_data):
        print(f'Uploading {file_name}...')
        lock_service = ServerProxy(self.secure_server_url)
        lock_service.acquire(file_name)
        
        # 写入本地
        file_path = os.path.join(self.master_dir, file_name)
        with open(file_path, 'w') as file:
            file.write(file_data)

        # 分发文件到其他从服务器
        print(f'Synchronizing {file_name} to the slave servers...')
        for slave_url in self.slave_urls:
            slave_proxy = ServerProxy(slave_url)
            try:
                ret = slave_proxy.upload_file(file_name, file_data)
                if not ret:
                    return False
            except Exception as e:
                # 服务器断开连接，从服务器列表删除
                print(f"Error connecting to {slave_url}: {e}")
                if slave_url in self.slave_urls:
                    self.slave_urls.remove(slave_url)
        print(f'Successfully Synchronize {file_name}')

        # 如果不在目录中就加上
        if file_name not in self.file_directory:
            self.file_directory.append(file_name)
            with self.dir_lock, open(os.path.join(self.master_dir, 'directory.txt'), 'a+') as f:
                f.write(f'{file_name}\n')

        lock_service.release(file_name)
        print(f'Successfully upload {file_name}')
        return True
    
    def delete_file(self, file_name):
        file_path = os.path.join(self.master_dir, file_name)
        if not os.path.exists(file_path):
            return False
        
        # 获取文件锁
        lock_service = ServerProxy(self.secure_server_url)
        lock_service.acquire(file_name)

        print(f'Deleting {file_name}...')
        # 删除本地文件
        os.remove(file_path)

        # 告知所有从服务器删除文件
        for slave_url in self.slave_urls:
            slave_proxy = ServerProxy(slave_url)
            try:
                ret = slave_proxy.delete_file(file_name)
                if not ret:
                    return False
            except Exception as e:
                # 服务器断开连接，从服务器列表删除
                print(f"Error connecting to {slave_url}: {e}")
                if slave_url in self.slave_urls:
                    self.slave_urls.remove(slave_url)

        # 删除目录列表和目录文件中的相关项
        self.file_directory.remove(file_name)
        with self.dir_lock, open(os.path.join(self.master_dir, 'directory.txt'), 'w+') as f:
            for item in self.file_directory:
                f.write(f'{item}\n')

        lock_service.release(file_name)
        print(f'Successfully delete {file_name}')
        return True
    
    def create_file(self, file_name):
        file_path = os.path.join(self.master_dir, file_name)
        if os.path.exists(file_path):
            return False
        
        # 获取文件锁
        lock_service = ServerProxy(self.secure_server_url)
        lock_service.acquire(file_name)

        print(f'Creating {file_name}...')
        # 创建本地文件
        with open(file_path, 'w') as f:
            pass  # 创建一个空文件

        # 告知所有从服务器创建文件
        for slave_url in self.slave_urls:
            slave_proxy = ServerProxy(slave_url)
            try:
                ret = slave_proxy.create_file(file_name)
                if not ret:
                    return False
            except Exception as e:
                # 服务器断开连接，从服务器列表删除
                print(f"Error connecting to {slave_url}: {e}")
                if slave_url in self.slave_urls:
                    self.slave_urls.remove(slave_url)
        
        # 更新目录列表和目录文件
        self.file_directory.append(file_name)
        with self.dir_lock, open(os.path.join(self.master_dir, 'directory.txt'), 'a+') as f:
            f.write(f'{file_name}\n')

        lock_service.release(file_name)
        print(f'Successfully creating {file_name}')
        return True
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start the program with optional port number and slave count.')
    parser.add_argument('--port', type=int, default=8888, help='Specify the port number (default: 8888)')
    args = parser.parse_args()

    port = args.port

    server = MasterServer('localhost', port)
    server.start()