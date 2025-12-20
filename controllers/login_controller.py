#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录控制器
处理用户登录、注册等业务逻辑
"""

from typing import Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal

from models.user import User, UserManager
from models.config import ConfigManager


class LoginController(QObject):
    """登录控制器类"""
    
    # 信号定义
    login_success = pyqtSignal(str)  # 登录成功信号，参数为用户名
    login_failed = pyqtSignal(str)   # 登录失败信号，参数为错误信息
    register_success = pyqtSignal()  # 注册成功信号
    register_failed = pyqtSignal(str)  # 注册失败信号，参数为错误信息
    
    def __init__(self):
        super().__init__()
        self.user_manager = UserManager()
        self.config_manager = ConfigManager()
        self._init_default_users()
    
    def _init_default_users(self):
        """初始化默认用户"""
        default_users = self.config_manager.get_config().users.valid_users
        for username, password in default_users.items():
            user = User(username=username, password=password)
            self.user_manager.add_user(user)
    
    def login(self, username: str, password: str, server_host: str, server_port: int) -> bool:
        """处理用户登录"""
        # 验证输入
        if not username or not password:
            self.login_failed.emit("请输入用户名和密码")
            return False
        
        if not server_host or not server_port:
            self.login_failed.emit("请输入服务器地址和端口")
            return False
        
        try:
            port_num = int(server_port)
            if port_num < 1 or port_num > 65535:
                self.login_failed.emit("端口号必须是1-65535之间的数字")
                return False
        except ValueError:
            self.login_failed.emit("端口号必须是数字")
            return False
        
        # 验证用户
        if self.user_manager.authenticate(username, password):
            self.login_success.emit(username)
            return True
        else:
            self.login_failed.emit("用户名或密码错误")
            return False
    
    def register(self, username: str, password: str, email: str = "", nickname: str = "") -> bool:
        """处理用户注册"""
        # 验证输入
        if not username or not password:
            self.register_failed.emit("用户名和密码不能为空")
            return False
        
        if len(password) < 6:
            self.register_failed.emit("密码长度不能少于6位")
            return False
        
        if self.user_manager.user_exists(username):
            self.register_failed.emit("用户名已存在")
            return False
        
        try:
            # 创建新用户
            user = User(
                username=username,
                password=password,
                email=email if email else None,
                nickname=nickname if nickname else None
            )
            
            # 添加到用户管理器
            if self.user_manager.add_user(user):
                self.register_success.emit()
                return True
            else:
                self.register_failed.emit("注册失败，请重试")
                return False
        except Exception as e:
            self.register_failed.emit(f"注册失败: {str(e)}")
            return False
    
    def get_server_config(self) -> tuple[str, int]:
        """获取服务器配置"""
        config = self.config_manager.get_config()
        return config.client.default_server_host, config.client.default_server_port
    
    def save_server_config(self, host: str, port: int) -> bool:
        """保存服务器配置"""
        try:
            config = self.config_manager.get_config()
            config.client.default_server_host = host
            config.client.default_server_port = port
            return self.config_manager.save_config()
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get_user_list(self) -> list[str]:
        """获取用户列表"""
        return self.user_manager.get_all_usernames()
