#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络管理器
负责客户端与服务器之间的网络通信
"""

from typing import Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import socket
import json
import time
import os
from datetime import datetime

from client.models.vo import MessageVO, FileVO, UserVO


class NetworkThread(QThread):
    """网络通信线程类，负责与服务器通信"""
    # 信号定义
    message_received = pyqtSignal(object)      # 接收到的消息(VO对象)
    user_list_updated = pyqtSignal(list)       # 用户列表更新
    connection_status = pyqtSignal(bool, str)  # 连接状态, 消息
    file_received = pyqtSignal(str, str)       # 文件名, 文件路径
    login_response = pyqtSignal(bool, str)     # 登录响应(成功/失败, 消息)
    register_response = pyqtSignal(bool, str)  # 注册响应(成功/失败, 消息)
    
    def __init__(self, server_host: str, server_port: int):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None
        self.running = False
        self.buffer_size = 1024
        self.username = None
        
    def run(self):
        try:
            # 创建TCP连接
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10)
            self.client_socket.connect((self.server_host, self.server_port))
            
            self.running = True
            self.connection_status.emit(True, "连接成功")
            
            # 开始接收消息
            while self.running:
                try:
                    data = self.receive_data()
                    if data:
                        self.handle_message(data)
                    else:
                        break
                except socket.timeout:
                    continue
                except Exception as e:
                    break
        except Exception as e:
            self.connection_status.emit(False, f"连接失败: {str(e)}")
        finally:
            self.close_connection()
    
    def handle_message(self, data: dict):
        """处理接收到的消息"""
        msg_type = data.get('type')
        
        if msg_type == 'message':
            username = data.get('username', '')
            message = data.get('message', '')
            timestamp = data.get('timestamp', time.time())
            
            # 创建消息VO对象用于界面展示
            message_vo = MessageVO(
                message_id=data.get('message_id', ''),
                user_id=data.get('user_id', ''),
                username=username,
                content_type="text",
                content=message,
                created_at=datetime.fromtimestamp(timestamp) if timestamp else None
            )
            
            self.message_received.emit(message_vo)
            
        elif msg_type == 'user_list':
            users = data.get('users', [])
            self.user_list_updated.emit(users)
            
        elif msg_type == 'file':
            filename = data.get('filename', '')
            file_data = data.get('data', '')
            file_size = data.get('size', 0)
            
            # 保存文件
            file_path = self.save_file(filename, file_data)
            if file_path:
                self.file_received.emit(filename, file_path)
                
        elif msg_type == 'login_success':
            self.username = data.get('username', '')
            self.login_response.emit(True, "登录成功")
            
        elif msg_type == 'login_failed':
            self.login_response.emit(False, data.get('message', '登录失败'))
            
        elif msg_type == 'register_success':
            self.register_response.emit(True, "注册成功")
            
        elif msg_type == 'register_failed':
            self.register_response.emit(False, data.get('message', '注册失败'))
    
    def login(self, username: str, password: str) -> None:
        """发送登录请求"""
        if self.client_socket and self.running:
            login_data = {
                'type': 'login',
                'username': username,
                'password': password
            }
            self.send_data(login_data)
    
    def register(self, user_vo: UserVO) -> None:
        """发送注册请求"""
        if self.client_socket and self.running:
            data = user_vo.to_dict()
            data['type'] = 'register'

            self.send_data(data)
    
    def send_message(self, message_vo: MessageVO) -> bool:
        """发送消息"""
        if self.client_socket and self.running:
            # 将VO对象转换为字典进行传输
            data = message_vo.to_dict()
            data['type'] = 'message'  # 添加消息类型标识
            
            self.send_data(data)
            return True
        return False
    
    def send_file(self, file_path: str) -> bool:
        """发送文件"""
        if not self.client_socket or not self.running:
            return False
        
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # 检查文件大小
            max_file_size = 10 * 1024 * 1024  # 10MB
            if len(file_data) > max_file_size:
                print(f"文件大小超过限制: {len(file_data)} > {max_file_size}")
                return False
            
            filename = os.path.basename(file_path)
            
            # 创建文件VO对象
            file_vo = FileVO(
                file_id="",  # 会在服务端生成
                file_name=filename,
                file_url="",  # 会在服务端生成
                file_type="file",
                file_size=len(file_data),
                created_at=datetime.now()
            )
            
            # 将VO对象转换为字典进行传输
            data = file_vo.to_dict()
            data.update({
                'type': 'file',
                'data': file_data.decode('latin-1'),  # 转换为字符串传输
                'size': len(file_data)
            })
            
            self.send_data(data)
            return True
        except Exception as e:
            print(f"发送文件失败: {e}")
            return False
    
    def send_data(self, data: dict):
        """发送数据到服务器"""
        if self.client_socket:
            json_data = json.dumps(data)
            self.client_socket.send(json_data.encode('utf-8'))
    
    def receive_data(self) -> Optional[dict]:
        """从服务器接收数据"""
        if self.client_socket:
            data = self.client_socket.recv(self.buffer_size)
            if data:
                json_data = data.decode('utf-8')
                return json.loads(json_data)
        return None
    
    def save_file(self, filename: str, file_data: str) -> Optional[str]:
        """保存接收到的文件"""
        try:
            # 创建接收文件目录
            download_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'ChatRoom')
            os.makedirs(download_dir, exist_ok=True)
            
            file_path = os.path.join(download_dir, filename)
            
            # 如果文件已存在，添加时间戳
            if os.path.exists(file_path):
                name, ext = os.path.splitext(filename)
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                file_path = os.path.join(download_dir, f"{name}_{timestamp}{ext}")
            
            with open(file_path, 'wb') as f:
                f.write(file_data.encode('latin-1'))
            
            return file_path
        except Exception as e:
            print(f"保存文件失败: {e}")
            return None
    
    def close_connection(self):
        """关闭连接"""
        self.running = False
        if self.client_socket:
            try:
                # 发送退出消息
                logout_data = {'type': 'logout'}
                self.send_data(logout_data)
            except:
                pass
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None


class NetworkManager(QObject):
    """网络管理器类（单例模式）"""
    
    # 信号定义
    message_received = pyqtSignal(object)      # 接收到的消息(VO对象)
    user_list_updated = pyqtSignal(list)       # 用户列表更新
    connection_status = pyqtSignal(bool, str)  # 连接状态, 消息
    file_received = pyqtSignal(str, str)       # 文件名, 文件路径
    login_response = pyqtSignal(bool, str)     # 登录响应(成功/失败, 消息)
    register_response = pyqtSignal(bool, str)  # 注册响应(成功/失败, 消息)
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            super().__init__()
            self.network_thread: Optional[NetworkThread] = None
            self.connected = False
            self.server_host = None
            self.server_port = None
            self.username = None
            self._initialized = True
    
    def connect_to_server(self, server_host: str, server_port: int) -> bool:
        """连接到服务器"""
        self.server_host = server_host
        self.server_port = server_port
        
        # 启动网络线程
        self.network_thread = NetworkThread(server_host, server_port)
        self.network_thread.message_received.connect(self.on_message_received)
        self.network_thread.user_list_updated.connect(self.on_user_list_updated)
        self.network_thread.connection_status.connect(self.on_connection_status)
        self.network_thread.file_received.connect(self.on_file_received)
        self.network_thread.login_response.connect(self.on_login_response)
        self.network_thread.register_response.connect(self.on_register_response)
        self.network_thread.start()
        
        return True
    
    def disconnect_from_server(self):
        """断开与服务器的连接"""
        if self.network_thread:
            self.network_thread.close_connection()
            self.network_thread = None
        self.connected = False
        self.username = None
    
    def login(self, username: str, password: str) -> None:
        """用户登录"""
        if self.network_thread and self.connected:
            self.network_thread.login(username, password)
        else:
            self.login_response.emit(False, "未连接到服务器")
    
    def register(self, user_vo: UserVO) -> None:
        """用户注册"""
        if self.network_thread and self.connected:
            self.network_thread.register(user_vo)
        else:
            self.register_response.emit(False, "未连接到服务器")
    
    def send_message(self, message_vo: MessageVO) -> bool:
        """发送消息"""
        if self.network_thread and self.connected:
            return self.network_thread.send_message(message_vo)
        return False
    
    def send_file(self, file_path: str) -> bool:
        """发送文件"""
        if self.network_thread and self.connected:
            return self.network_thread.send_file(file_path)
        return False
    
    def on_message_received(self, message_vo):
        """处理接收到的消息"""
        self.message_received.emit(message_vo)
    
    def on_user_list_updated(self, users: list):
        """处理用户列表更新"""
        self.user_list_updated.emit(users)
    
    def on_connection_status(self, success: bool, message: str):
        """处理连接状态变化"""
        self.connected = success
        self.connection_status.emit(success, message)
    
    def on_file_received(self, filename: str, file_path: str):
        """处理接收到的文件"""
        self.file_received.emit(filename, file_path)
    
    def on_login_response(self, success: bool, message: str):
        """处理登录响应"""
        if success:
            # 可以在这里保存用户名等信息
            pass
        self.login_response.emit(success, message)
    
    def on_register_response(self, success: bool, message: str):
        """处理注册响应"""
        self.register_response.emit(success, message)