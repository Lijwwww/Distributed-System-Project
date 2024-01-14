## 分布式系统大作业——分布式文件系统

#### 架构介绍
1. 主服务器（MasterServer）
   承担与客户通信、存储数据、维护文件目录、管理从服务器、同步数据到从服务器五个任务。
2. 从服务器（SlaveServer）
   从服务器承担与主服务器保持同步、服务客户端读操作等任务。
3. 安全服务器（SecureServer）
   安全服务器承担两个任务：用户登录注册和文件锁的提供。
4. 客户端（Client）
   客户端以命令行的方式接收用户的键盘输入，并进行相应操作。

#### 启动方法
1. 启动主服务器
   `python MasterServer.py --port [port]`
2. 启动安全服务器
   `python SecureServer.py --port [port]`
3. 启动从服务器
   `python SlaveServer.py <slave_id> --base_port [base_port]`
4. 客户端注册
   `python Client.py signup <username> <password> --port [port]`
5. 客户端登录
   `python Client.py login <username> <password> --port [port]`
6. 文件操作
```
- ls: List files on the server
- download <file_name>: Download a file from the server
- upload <file_name>: Upload a file to the server
- delete <file_name>: Delete a file on the server
- create <file_name>: Create a new file on the server
- open <file_name>: Open a file on the server
- help: Show this help message
- exit: Exit the program
```