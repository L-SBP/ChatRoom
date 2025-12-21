#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码工具类
提供密码加密和验证功能
"""

import hashlib
import base64
from typing import Tuple

from common.config import get_server_config

server_config = get_server_config()


class PasswordUtils:
    """
    密码工具类
    提供密码加密、验证和盐值生成等功能
    """
    
    @staticmethod
    def get_salt() -> str:
        """
        从配置中获取固定盐值
        
        Returns:
            str: 配置中的固定盐值
        """
        # 修复：使用正确的变量名 server_config 而不是 config
        return server_config.security.password_salt
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        对密码进行哈希处理
        
        Args:
            password: 原始密码
            
        Returns:
            str: 哈希密码
        """
        salt = PasswordUtils.get_salt()
        
        # 将盐值和密码组合后进行哈希
        salt_bytes = salt.encode('utf-8')
        password_bytes = password.encode('utf-8')
        
        # 使用PBKDF2进行密码哈希
        pwdhash = hashlib.pbkdf2_hmac('sha256', password_bytes, salt_bytes, 100000)
        hashed_password = base64.b64encode(pwdhash).decode('utf-8')
        
        return hashed_password
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        验证密码是否正确
        
        Args:
            password: 待验证的原始密码
            hashed_password: 存储的哈希密码
            
        Returns:
            bool: 密码正确返回True，否则返回False
        """
        # 使用相同的盐值对输入密码进行哈希
        rehashed_password = PasswordUtils.hash_password(password)
        
        # 比较哈希值
        return rehashed_password == hashed_password
    
    @staticmethod
    def is_password_strong(password: str) -> bool:
        """
        检查密码强度
        
        Args:
            password: 待检查的密码
            
        Returns:
            bool: 密码强度满足要求返回True，否则返回False
        """
        # 从配置中获取密码强度要求
        # 当前默认要求至少6位字符
        min_length = 6
        return len(password) >= min_length

password_utils = PasswordUtils()