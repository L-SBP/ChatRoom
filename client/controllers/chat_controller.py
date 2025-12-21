#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天控制器
处理聊天相关的业务逻辑
"""

from typing import List, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime
import os

# 使用VO模型和网络管理器
from client.models.vo import MessageVO, FileVO
from client.network.network_manager import NetworkManager


class ChatController(QObject):
    """聊天控制器类"""
    
    # 信号定义 - 使用VO对象（用于界面展示）
    connection_established = pyqtSignal()  # 连接建立成功
    connection_failed = pyqtSignal(str)    # 连接失败
    message_sent = pyqtSignal(object)     # 消息发送成功(VO对象)
    message_received = pyqtSignal(object) # 接收到消息(VO对象)
    user_list_updated = pyqtSignal(list)   # 用户列表更新
    file_sent = pyqtSignal(str)            # 文件发送成功
    file_received = pyqtSignal(str, str)   # 文件接收成功
    system_message = pyqtSignal(str)       # 系统消息
    
    def __init__(self):
        super().__init__()
        # 使用网络管理器（单例模式）
        self.network_manager = NetworkManager()
        self.network_manager.message_received.connect(self.on_message_received)
        self.network_manager.user_list_updated.connect(self.on_user_list_updated)
        self.network_manager.connection_status.connect(self.on_connection_status)
        self.network_manager.file_received.connect(self.on_file_received)
        
        self.connected = False
        self.current_user = None
        self.server_host = None
        self.server_port = None
        self.online_users = []
    
    def connect_to_server(self, server_host: str, server_port: int, username: str, password: str) -> bool:
        """连接到服务器并登录"""
        self.server_host = server_host
        self.server_port = server_port
        self.current_user = username
        
        # 检查是否已经连接
        if self.network_manager.is_connected():
            # 已经连接，直接登录
            self.network_manager.login(username, password)
            return True
        else:
            # 尚未连接，先建立连接
            success = self.network_manager.connect_to_server(server_host, server_port)
            if success:
                # 连接成功后进行登录
                self.network_manager.login(username, password)
            return success
    
    def disconnect_from_server(self):
        """断开与服务器的连接"""
        self.network_manager.disconnect_from_server()
        self.connected = False
        self.current_user = None
        self.online_users = []
    
    def send_message(self, content: str, receiver: str = None) -> bool:
        """发送消息"""
        if not self.connected:
            self.system_message.emit("未连接到服务器")
            return False
        
        # 创建消息VO对象用于界面展示
        message_vo = MessageVO(
            message_id="",  # 会在服务端生成
            user_id="",     # 会在服务端设置
            username=self.current_user,
            content_type="text",
            content=content,
            created_at=datetime.now()
        )
        
        # 通过网络管理器发送消息
        success = self.network_manager.send_message(message_vo)
        if success:
            self.message_sent.emit(message_vo)
        else:
            self.system_message.emit("消息发送失败")
        
        return success
    
    def send_file(self, file_path: str) -> bool:
        """发送文件"""
        if not self.connected:
            self.system_message.emit("未连接到服务器")
            return False
        
        success = self.network_manager.send_file(file_path)
        if success:
            self.file_sent.emit(os.path.basename(file_path))
        else:
            self.system_message.emit("文件发送失败")
        
        return success
    
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
        # 可以在这里向服务器发送刷新请求
        pass
    
    def on_message_received(self, message_vo):
        """处理接收到的消息"""
        # 发射信号给视图层
        self.message_received.emit(message_vo)
    
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
