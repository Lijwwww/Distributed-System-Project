from xmlrpc.client import ServerProxy
import os
from random import randint
import argparse

CLIENT_DIR = "ClientFiles"
os.makedirs(CLIENT_DIR, exist_ok=True)

class ClientProxy:
    def __init__(self, auth_server_url):
        self.auth_proxy = ServerProxy(auth_server_url)
        self.cache_capacity = 5

    def list_files(self):
        try:
            files = self.proxy.list_files()
            print(f'Files on server: {", ".join(files)}')
        except Exception as e:
            print('Error get directory: {e}')

    def download_file(self, file_name, save_path='default'):
        # 接收主服务器发来的服务器url列表和安全服务器url
        try:
            info = self.proxy.request_download_file(file_name)
            if not info:
                print('Error: No such file or directory')
                return False

        except Exception as e:
            print('Error uploading file: {e}')
            return False
        
        # 用户键盘输入，直到输入合法为止
        while True:
            try:
                num = int(input(f'Choose the server to pull the file, from Server 0 to {len(info[0])-1}: '))
                if 0 <= num < len(info[0]):
                    break  # 输入合法，退出循环
                else:
                    print(f'Invalid input. Please enter a number between 0 and {len(info[0])-1}.')
            except ValueError:
                print('Invalid input. Please enter a valid number.')

        # 获取安全服务器和目标服务器代理
        lock_service = ServerProxy(info[1])
        download_service = ServerProxy(info[0][num])

        try:
            lock_service.acquire(file_name)
        except Exception as e:
            # 与安全服务器连接失败
            print(f"Error connecting to SecureServer")
            return False

        try:
            file_data = download_service.download_file(file_name)
        except Exception as e:
            # 与文件服务器连接失败
            print(f"Error connecting to {info[0][num]}: {e}")
            return False

        if not file_data:
            print('Error: No such file or directory')
        else:
            # 写入本地下载目录
            if save_path == 'default':
                save_path = os.path.join(self.client_dir, file_name)  
                # 如果缓存有该文件，则删除
                if file_name in os.listdir(self.cache_dir):
                    os.remove(os.path.join(self.cache_dir, file_name))    
                       
            with open(save_path, 'w') as local_file:
                local_file.write(file_data)
        
        try:
            lock_service.release(file_name)
        except Exception as e:
            # 与安全服务器连接失败
            print(f"Error connecting to SecureServer")
            return False
        
        print('Download Finished')
        return True
    

    def upload_file(self, file_name):
        try:
            file_path = os.path.join(self.client_dir, file_name)
            with open(file_path, 'r') as local_file:
                file_data = local_file.read()
                self.proxy.upload_file(file_name, file_data)
            print('Upload finished')
        except Exception as e:
            print('Error uploading file: {e}')
    
    def delete_file(self, file_name):
        try:
            ret = self.proxy.delete_file(file_name)
            if ret:
                print('Delete finished')
            else:
                print('Error: No such file or directory')
        except Exception as e:
            print('Error uploading file: {e}')

    def create_file(self, file_name):
        try:
            ret = self.proxy.create_file(file_name)
            if ret:
                print('Create finished')
            else:
                print(f'Error: {file_name} already exists')
        except Exception as e:
            print('Error creating file: {e}')

    def open_file(self, file_name):
        cache_file_path = os.path.join(self.cache_dir, file_name)
        file_path = os.path.join(self.client_dir, file_name)
        # 在本地下载目录有直接打开
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    print(line)
            return
          
        # 在本地下载目录和缓存都没有
        elif not os.path.exists(cache_file_path):
            print('Local cache does not have the file. Download required.')
            # 若缓存满则先删除一个文件
            files = os.listdir(self.cache_dir)
            if len(files) >= self.cache_capacity:
                delete_file_path = os.path.join(self.cache_dir, files[0])
                os.remove(delete_file_path)
                print(f"Cache is full, delete file: {delete_file_path}")
            # 下载文件到缓存
            if not self.download_file(file_name, cache_file_path):
                return

        # 打开缓存文件
        with open(cache_file_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                print(line)  

    def login(self, username, password):
        try:
            ret = self.auth_proxy.login(username, password)
            if not ret:
                print('Username or password incorrect.')
                exit(0)
            else:
                # 登陆成功，创建该用户的文件夹
                self.proxy = ServerProxy(ret)
                self.client_dir = os.path.join(CLIENT_DIR, username)
                os.makedirs(self.client_dir, exist_ok=True)
                self.cache_dir = os.path.join(self.client_dir, "cache")
                os.makedirs(self.cache_dir, exist_ok=True)
                print(f'Connect to master: {ret}')
        except Exception as e:
            print('Error connecting to AuthServer.')
            exit(0)
    
    def signup(self, username, password):
        try:
            ret = self.auth_proxy.signup(username, password)
            if not ret:
                print('Username is used.')
            else:
                print('Successfully signup!')
            exit(0)

        except Exception as e:
            print('Error connecting to AuthServer.')
            exit(0)

def print_welcome():
    print("========== Welcome to Distributed File System ==========")
    print("This is a simple file management system.")
    print("Use the following commands to interact with the system:")
    print("  - ls: List files on the server")
    print("  - download <file_name>: Download a file from the server")
    print("  - upload <file_name>: Upload a file to the server")
    print("  - delete <file_name>: Delete a file on the server")
    print("  - create <file_name>: Create a new file on the server")
    print("  - open <file_name>: Open a file on the server")
    print("  - help: Show this help message")
    print("  - exit: Exit the program")
    print("========================================================")

def print_help():
    print("========== Help ==========")
    print("ls - List files on the server")
    print("download <file_name> - Download a file from the server")
    print("upload <file_name> - Upload a file to the server")
    print("delete <file_name> - Delete a file on the server")
    print("create <file_name> - Create a new file on the server")
    print("open <file_name> - Open a file on the server")
    print("exit - Exit the program")
    print("==========================")

def main():
    parser = argparse.ArgumentParser(description="RPC Client")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 注册命令
    signup_parser = subparsers.add_parser("signup", help="Signup command")
    signup_parser.add_argument("username", type=str, help="Username")
    signup_parser.add_argument("password", type=str, help="Password")
    signup_parser.add_argument("--port", type=int, default=8889, help="port")

    # 登录命令
    login_parser = subparsers.add_parser("login", help="Login command")
    login_parser.add_argument("username", type=str, help="Username")
    login_parser.add_argument("password", type=str, help="Password")
    login_parser.add_argument("--port", type=int, default=8889, help="port")

    args = parser.parse_args()

    client = ClientProxy(f"http://localhost:{args.port}")

    if args.command == "signup":
        client.signup(args.username, args.password)
    elif args.command == "login":
        client.login(args.username, args.password)
    else:
        parser.print_help()

    print_welcome()

    while True:
        command = input(">> ")
        
        if command == "exit":
            print("Exiting...")
            break
        elif command == "ls":
            client.list_files()
        elif command.startswith("download "):
            if len(command.split(" ")) != 2:
                print("Error: Incorrect number of arguments for download command.")
            else:
                file_name = command.split(" ")[1]
                # save_path = input("Enter the save path: ")
                client.download_file(file_name)
        elif command.startswith("upload "):
            if len(command.split(" ")) != 2:
                print("Error: Incorrect number of arguments for upload command.")
            else:
                file_name = command.split(" ")[1]
                client.upload_file(file_name)
        elif command.startswith("delete "):
            if len(command.split(" ")) != 2:
                print("Error: Incorrect number of arguments for delete command.")
            else:
                file_name = command.split(" ")[1]
                client.delete_file(file_name)
        elif command.startswith("create "):
            if len(command.split(" ")) != 2:
                print("Error: Incorrect number of arguments for create command.")
            else:
                file_name = command.split(" ")[1]
                client.create_file(file_name)
        elif command.startswith("open "):
            if len(command.split(" ")) != 2:
                print("Error: Incorrect number of arguments for open command.")
            else:
                file_name = command.split(" ")[1]
                client.open_file(file_name)
        elif command == "help":
            print_help()
        else:
            print("Invalid command. Try 'help' for command information.")

if __name__ == "__main__":
    main()