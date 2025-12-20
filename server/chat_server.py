#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天室服务器
基于TCP协议的多客户端聊天服务器
"""

import socket
import threading
import json
import time
import logging
from typing import Dict, List, Tuple

# 导入配置
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config.config import config


class ChatServer:
    """聊天服务器类"""
    
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.clients: Dict[str, socket.socket] = {}  # 用户名 -> socket
        self.client_info: Dict[str, Dict] = {}  # 用户名 -> 详细信息
        self.running = False
        self.server_socket = None
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """启动服务器"""
        try:
            # 创建服务器socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 绑定地址和端口
            self.server_socket.bind((self.host, self.port))
            
            # 开始监听
            self.server_socket.listen(5)
            self.running = True
            
            self.logger.info(f"服务器启动成功，监听地址: {self.host}:{self.port}")
            print(f"服务器启动成功，监听地址: {self.host}:{self.port}")
            print("等待客户端连接...")
            
            # 接受客户端连接
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    self.logger.info(f"新连接来自: {client_address}")
                    
                    # 为每个客户端创建新线程
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        self.logger.error(f"接受连接时出错: {e}")
                        
        except Exception as e:
            self.logger.error(f"服务器启动失败: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止服务器"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        self.logger.info("服务器已停止")
    
    def handle_client(self, client_socket: socket.socket, address: Tuple[str, int]):
        """处理客户端连接"""
        username = None
        try:
            while self.running:
                try:
                    # 接收数据
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # 解析JSON数据
                    message = json.loads(data.decode('utf-8'))
                    msg_type = message.get('type')
                    
                    if msg_type == 'login':
                        # 处理登录
                        username = message.get('username')
                        password = message.get('password')
                        
                        if self.authenticate_user(username, password):
                            if username in self.clients:
                                # 用户已存在
                                response = {
                                    'type': 'login_failed',
                                    'message': '用户已在其他地方登录'
                                }
                                client_socket.send(json.dumps(response).encode('utf-8'))
                                client_socket.close()
                                return
                            
                            # 登录成功
                            self.clients[username] = client_socket
                            self.client_info[username] = {
                                'address': address,
                                'login_time': time.time(),
                                'socket': client_socket
                            }
                            
                            response = {
                                'type': 'login_success',
                                'message': '登录成功',
                                'username': username
                            }
                            client_socket.send(json.dumps(response).encode('utf-8'))
                            
                            # 发送用户列表
                            self.send_user_list()
                            
                            # 发送欢迎消息
                            self.broadcast_system_message(f"{username} 加入了聊天室")
                            self.logger.info(f"用户 {username} 登录成功")
                            break
                        else:
                            # 登录失败
                            response = {
                                'type': 'login_failed',
                                'message': '用户名或密码错误'
                            }
                            client_socket.send(json.dumps(response).encode('utf-8'))
                            client_socket.close()
                            return
                    
                    elif msg_type == 'logout':
                        # 处理退出
                        if username:
                            self.remove_client(username, "主动退出")
                        break
                    
                    else:
                        # 其他消息需要先登录
                        response = {
                            'type': 'error',
                            'message': '请先登录'
                        }
                        client_socket.send(json.dumps(response).encode('utf-8'))
                        
                except json.JSONDecodeError:
                    self.logger.warning(f"客户端 {address} 发送的数据格式错误")
                except Exception as e:
                    self.logger.error(f"处理客户端 {address} 消息时出错: {e}")
                    break
            
            # 处理消息循环
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    message = json.loads(data.decode('utf-8'))
                    msg_type = message.get('type')
                    
                    if msg_type == 'message':
                        # 处理普通消息
                        self.handle_message(username, message)
                    
                    elif msg_type == 'file':
                        # 处理文件
                        self.handle_file(username, message)
                    
                    elif msg_type == 'refresh_users':
                        # 刷新用户列表
                        self.send_user_list_to_client(client_socket)
                    
                    elif msg_type == 'logout':
                        # 处理退出
                        self.remove_client(username, "主动退出")
                        break
                
                except json.JSONDecodeError:
                    self.logger.warning(f"客户端 {address} 发送的数据格式错误")
                except Exception as e:
                    self.logger.error(f"处理客户端 {address} 消息时出错: {e}")
                    break
        
        except Exception as e:
            self.logger.error(f"处理客户端 {address} 时出错: {e}")
        finally:
            if username:
                self.remove_client(username, "连接断开")
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """用户认证（从配置文件读取用户信息）"""
        if not username or not password:
            return False
        
        # 从配置文件获取有效用户
        valid_users = config.users.valid_users
        
        return username in valid_users and valid_users[username] == password
    
    def handle_message(self, username: str, message: dict):
        """处理消息"""
        if not username or username not in self.clients:
            return
        
        # 获取消息内容
        msg_content = message.get('message', '')
        timestamp = message.get('timestamp', time.time())
        
        if not msg_content:
            return
        
        # 广播消息给所有客户端
        self.broadcast_message(username, msg_content, timestamp)
    
    def handle_file(self, username: str, file_message: dict):
        """处理文件"""
        if not username or username not in self.clients:
            return
        
        # 获取文件信息
        filename = file_message.get('filename', '')
        file_data = file_message.get('data', '')
        file_size = file_message.get('size', 0)
        
        if not filename or not file_data:
            return
        
        # 广播文件给所有客户端
        self.broadcast_file(username, filename, file_data, file_size)
        
        self.logger.info(f"用户 {username} 发送文件: {filename} ({file_size} bytes)")
    
    def broadcast_message(self, username: str, message: str, timestamp=None):
        """广播消息给所有客户端"""
        if timestamp is None:
            timestamp = time.time()
        
        # 构造消息
        broadcast_message = {
            'type': 'message',
            'username': username,
            'message': message,
            'timestamp': time.strftime('%H:%M:%S', time.localtime(timestamp))
        }
        
        # 发送给所有客户端
        disconnected_clients = []
        for client_name, client_socket in self.clients.items():
            try:
                client_socket.send(json.dumps(broadcast_message).encode('utf-8'))
            except Exception as e:
                self.logger.error(f"发送消息给用户 {client_name} 失败: {e}")
                disconnected_clients.append(client_name)
        
        # 移除断开连接的客户端
        for client_name in disconnected_clients:
            self.remove_client(client_name, "发送消息失败")
    
    def broadcast_file(self, username: str, filename: str, file_data: str, file_size: int):
        """广播文件给所有客户端"""
        # 构造文件消息
        file_message = {
            'type': 'file',
            'username': username,
            'filename': filename,
            'data': file_data,
            'size': file_size
        }
        
        # 发送给所有客户端
        disconnected_clients = []
        for client_name, client_socket in self.clients.items():
            try:
                client_socket.send(json.dumps(file_message).encode('utf-8'))
            except Exception as e:
                self.logger.error(f"发送文件给用户 {client_name} 失败: {e}")
                disconnected_clients.append(client_name)
        
        # 移除断开连接的客户端
        for client_name in disconnected_clients:
            self.remove_client(client_name, "发送文件失败")
    
    def broadcast_system_message(self, message: str):
        """广播系统消息"""
        broadcast_message = {
            'type': 'system',
            'message': message,
            'timestamp': time.strftime('%H:%M:%S', time.localtime())
        }
        
        disconnected_clients = []
        for client_name, client_socket in self.clients.items():
            try:
                client_socket.send(json.dumps(broadcast_message).encode('utf-8'))
            except Exception as e:
                self.logger.error(f"发送系统消息给用户 {client_name} 失败: {e}")
                disconnected_clients.append(client_name)
        
        # 移除断开连接的客户端
        for client_name in disconnected_clients:
            self.remove_client(client_name, "发送系统消息失败")
    
    def send_user_list(self):
        """发送用户列表给所有客户端"""
        users = list(self.clients.keys())
        
        user_list_message = {
            'type': 'user_list',
            'users': users
        }
        
        disconnected_clients = []
        for client_name, client_socket in self.clients.items():
            try:
                client_socket.send(json.dumps(user_list_message).encode('utf-8'))
            except Exception as e:
                self.logger.error(f"发送用户列表给用户 {client_name} 失败: {e}")
                disconnected_clients.append(client_name)
        
        # 移除断开连接的客户端
        for client_name in disconnected_clients:
            self.remove_client(client_name, "发送用户列表失败")
    
    def send_user_list_to_client(self, client_socket: socket.socket):
        """发送用户列表给指定客户端"""
        users = list(self.clients.keys())
        
        user_list_message = {
            'type': 'user_list',
            'users': users
        }
        
        try:
            client_socket.send(json.dumps(user_list_message).encode('utf-8'))
        except Exception as e:
            self.logger.error(f"发送用户列表失败: {e}")
    
    def remove_client(self, username: str, reason: str):
        """移除客户端"""
        if username in self.clients:
            client_socket = self.clients[username]
            try:
                client_socket.close()
            except:
                pass
            
            del self.clients[username]
            if username in self.client_info:
                del self.client_info[username]
            
            self.logger.info(f"用户 {username} 已断开连接 ({reason})")
            
            # 发送系统消息
            self.broadcast_system_message(f"{username} 离开了聊天室")
            
            # 发送更新的用户列表
            self.send_user_list()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='聊天室服务器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器监听地址')
    parser.add_argument('--port', type=int, default=8888, help='服务器监听端口')
    
    args = parser.parse_args()
    
    # 启动服务器
    server = ChatServer(args.host, args.port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        server.stop()
    except Exception as e:
        print(f"服务器运行出错: {e}")


if __name__ == "__main__":
    main()
