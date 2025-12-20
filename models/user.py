#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户模型类
定义用户数据结构和基本操作
"""

from dataclasses import dataclass
from typing import Optional
import hashlib


@dataclass
class User:
    """用户数据模型"""
    username: str
    password: str
    email: Optional[str] = None
    nickname: Optional[str] = None
    created_at: Optional[str] = None
    last_login: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.username or not self.password:
            raise ValueError("用户名和密码不能为空")
    
    def validate_password(self, password: str) -> bool:
        """验证密码是否正确"""
        return self.password == password
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'username': self.username,
            'password': self.password,
            'email': self.email,
            'nickname': self.nickname,
            'created_at': self.created_at,
            'last_login': self.last_login
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """从字典创建用户对象"""
        return cls(
            username=data.get('username', ''),
            password=data.get('password', ''),
            email=data.get('email'),
            nickname=data.get('nickname'),
            created_at=data.get('created_at'),
            last_login=data.get('last_login')
        )


class UserManager:
    """用户管理器"""
    
    def __init__(self):
        self.users: dict[str, User] = {}
    
    def add_user(self, user: User) -> bool:
        """添加用户"""
        if user.username in self.users:
            return False
        self.users[user.username] = user
        return True
    
    def get_user(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.users.get(username)
    
    def authenticate(self, username: str, password: str) -> bool:
        """用户认证"""
        user = self.get_user(username)
        if user and user.validate_password(password):
            return True
        return False
    
    def user_exists(self, username: str) -> bool:
        """检查用户是否存在"""
        return username in self.users
    
    def get_all_usernames(self) -> list[str]:
        """获取所有用户名列表"""
        return list(self.users.keys())
