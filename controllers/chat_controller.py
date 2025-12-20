#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天控制器
处理聊天相关的业务逻辑
"""

from typing import List, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import socket
import threading
import json
import time
import os

from models.message import Message, SystemMessage, FileMessage, MessageManager
from models.user import User


class CommunicationThread(QThread):
    """通信线程类，负责与服务器通信"""
    message_received = pyqtSignal(Message)  # 接收到的消息
    user_list_updated = pyqtSignal(list)    # 用户列表更新
    connection_status = pyqtSignal(bool, str)  # 连接状态, 消息
    file_received = pyqtSignal(str, str)    # 文件名, 文件路径
    
    def __init__(self, server_host: str, server_port: int, username: str, password: str):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.username = username
        self.password = password
        self.client_socket = None
        self.running = False
        self.buffer_size = 1024
        
    def run(self):
        try:
            # 创建TCP连接
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10)
            self.client_socket.connect((self.server_host, self.server_port))
            
            # 发送登录信息
            login_data = {
                'type': 'login',
                'username': self.username,
                'password': self.password
            }
            self.send_data(login_data)
            
            # 接收服务器响应
            response = self.receive_data()
            if response.get('type') == 'login_success':
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
            else:
                error_msg = response.get('message', '登录失败')
                self.connection_status.emit(False, error_msg)
                
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
            
            # 创建消息对象
            msg = Message(
                sender=username,
                content=message,
                timestamp=timestamp
            )
            self.message_received.emit(msg)
            
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
    
    def send_message(self, message: str) -> bool:
        """发送消息"""
        if self.client_socket and self.running:
            data = {
                'type': 'message',
                'message': message,
                'timestamp': time.time()
            }
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
            data = {
                'type': 'file',
                'filename': filename,
                'data': file_data.decode('latin-1'),  # 转换为字符串传输
                'size': len(file_data)
            }
            
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


class ChatController(QObject):
    """聊天控制器类"""
    
    # 信号定义
    connection_established = pyqtSignal()  # 连接建立成功
    connection_failed = pyqtSignal(str)    # 连接失败
    message_sent = pyqtSignal(Message)     # 消息发送成功
    message_received = pyqtSignal(Message) # 接收到消息
    user_list_updated = pyqtSignal(list)   # 用户列表更新
    file_sent = pyqtSignal(str)            # 文件发送成功
    file_received = pyqtSignal(str, str)   # 文件接收成功
    system_message = pyqtSignal(str)       # 系统消息
    
    def __init__(self):
        super().__init__()
        self.message_manager = MessageManager()
        self.communication_thread = None
        self.connected = False
        self.current_user = None
        self.server_host = None
        self.server_port = None
        self.online_users = []
    
    def connect_to_server(self, server_host: str, server_port: int, username: str, password: str) -> bool:
        """连接到服务器"""
        self.server_host = server_host
        self.server_port = server_port
        self.current_user = username
        
        # 启动通信线程
        self.communication_thread = CommunicationThread(
            server_host, server_port, username, password
        )
        self.communication_thread.message_received.connect(self.on_message_received)
        self.communication_thread.user_list_updated.connect(self.on_user_list_updated)
        self.communication_thread.connection_status.connect(self.on_connection_status)
        self.communication_thread.file_received.connect(self.on_file_received)
        self.communication_thread.start()
        
        return True
    
    def disconnect_from_server(self):
        """断开与服务器的连接"""
        if self.communication_thread:
            self.communication_thread.close_connection()
            self.communication_thread = None
        self.connected = False
        self.current_user = None
        self.online_users = []
    
    def send_message(self, content: str, receiver: str = None) -> bool:
        """发送消息"""
        if not self.connected or not self.communication_thread:
            self.system_message.emit("未连接到服务器")
            return False
        
        # 创建消息对象
        message = Message(
            sender=self.current_user,
            content=content,
            receiver=receiver
        )
        
        # 添加到消息管理器
        self.message_manager.add_message(message)
        
        # 发送到服务器
        success = self.communication_thread.send_message(content)
        if success:
            self.message_sent.emit(message)
        else:
            self.system_message.emit("消息发送失败")
        
        return success
    
    def send_file(self, file_path: str) -> bool:
        """发送文件"""
        if not self.connected or not self.communication_thread:
            self.system_message.emit("未连接到服务器")
            return False
        
        success = self.communication_thread.send_file(file_path)
        if success:
            self.file_sent.emit(os.path.basename(file_path))
        else:
            self.system_message.emit("文件发送失败")
        
        return success
    
    def get_message_history(self) -> List[Message]:
        """获取消息历史"""
        return self.message_manager.get_messages()
    
    def get_online_users(self) -> List[str]:
        """获取在线用户列表"""
        return self.online_users.copy()
    
    def start_private_chat(self, username: str) -> bool:
        """开始私聊"""
        if username == self.current_user:
            self.system_message.emit("不能与自己私聊")
            return False
        
        if username not in self.online_users:
            self.system_message.emit("用户不在线")
            return False
        
        # 可以在这里实现私聊逻辑
        self.system_message.emit(f"开始与 {username} 私聊")
        return True
    
    def refresh_user_list(self):
        """刷新用户列表"""
        if self.communication_thread and self.connected:
            # 发送刷新请求
            if self.communication_thread.client_socket:
                data = {'type': 'refresh_users'}
                try:
                    json_data = json.dumps(data)
                    self.communication_thread.client_socket.send(json_data.encode('utf-8'))
                except Exception as e:
                    print(f"刷新用户列表失败: {e}")
    
    def on_message_received(self, message: Message):
        """处理接收到的消息"""
        # 添加到消息管理器
        self.message_manager.add_message(message)
        
        # 发射信号
        self.message_received.emit(message)
    
    def on_user_list_updated(self, users: list):
        """处理用户列表更新"""
        self.online_users = users
        self.user_list_updated.emit(users)
    
    def on_connection_status(self, success: bool, message: str):
        """处理连接状态变化"""
        if success:
            self.connected = True
            self.connection_established.emit()
        else:
            self.connected = False
            self.connection_failed.emit(message)
    
    def on_file_received(self, filename: str, file_path: str):
        """处理接收到的文件"""
        self.file_received.emit(filename, file_path)
        self.system_message.emit(f"文件 '{filename}' 已接收并保存到: {file_path}")
