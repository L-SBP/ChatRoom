#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录控制器
处理用户登录业务逻辑
"""

from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal

# 使用VO模型和网络管理器
from client.models.vo import UserVO
from client.network.network_manager import NetworkManager
from common.config.client.config import get_client_config

# 获取客户端配置
client_config = get_client_config()


class LoginController(QObject):
    """登录控制器类"""
    
    # 信号定义
    login_success = pyqtSignal(str)  # 登录成功信号，参数为用户名
    login_failed = pyqtSignal(str)   # 登录失败信号，参数为错误信息
    
    def __init__(self):
        super().__init__()
        # 使用网络管理器（单例模式）
        self.network_manager = NetworkManager()
        self.network_manager.login_response.connect(self.on_login_response)
        self.network_manager.connection_status.connect(self.on_connection_status)
        
        # 使用UserVO
        self.current_user: Optional[UserVO] = None
        self.pending_login_credentials = None
        self.is_connecting = False  # 标记是否正在连接
    
    def login(self, username: str, password: str, server_host: str, server_port: int) -> bool:
        """处理用户登录"""
        # 验证输入
        if not username or not password:
            self.login_failed.emit("请输入用户名和密码")
            return False
        
        # 检查是否已经连接
        if self.network_manager.is_connected():
            # 已经连接，直接登录
            self.pending_login_credentials = (username, password)
            self.network_manager.login(username, password)
        else:
            # 尚未连接，先建立连接
            try:
                port_num = int(server_port)
                if port_num < 1 or port_num > 65535:
                    self.login_failed.emit("端口号必须是1-65535之间的数字")
                    return False
            except ValueError:
                self.login_failed.emit("端口号必须是数字")
                return False
            
            self.pending_login_credentials = (username, password)
            self.is_connecting = True
            success = self.network_manager.connect_to_server(server_host, port_num)
            if not success:
                self.login_failed.emit("无法连接到服务器")
                self.is_connecting = False
                self.pending_login_credentials = None
                return False
                
        return True
    
    def on_login_response(self, success: bool, message: str):
        """处理登录响应"""
        if success and self.pending_login_credentials:
            username, _ = self.pending_login_credentials
            # 在新的架构中，用户验证将在服务端进行
            # 这里我们假设验证成功并创建UserVO
            user_vo = UserVO(
                user_id="",
                username=username,
                password="",  # 不在VO中存储密码
                display_name=username,
                status="online"
            )
            
            # 登录用户
            self.current_user = user_vo
            self.login_success.emit(username)
        else:
            self.login_failed.emit(message)
        
        self.pending_login_credentials = None
        self.is_connecting = False
    
    def on_connection_status(self, success: bool, message: str):
        """处理连接状态变化"""
        if success and self.pending_login_credentials and self.is_connecting:
            # 连接成功，执行登录
            username, password = self.pending_login_credentials
            self.network_manager.login(username, password)
        elif not success:
            # 连接失败，重置状态
            self.login_failed.emit(f"连接失败: {message}")
            self.is_connecting = False
            self.pending_login_credentials = None
            # 连接失败时才断开连接
            self.network_manager.disconnect_from_server()
    
    def get_server_config(self) -> tuple[str, int]:
        """获取服务器配置"""
        return client_config.client.default_server_host, client_config.client.default_server_port
    
    def save_server_config(self, host: str, port: int) -> bool:
        """保存服务器配置"""
        try:
            from common.config.client.config import save_server_config
            save_server_config(host, port)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
