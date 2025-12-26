#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端管理器
管理所有客户端连接和用户信息
"""

import socket
from typing import Dict, List
from server.models.client import Client
from common.log import server_log as log


class ClientManager:
    """
    客户端管理器类
    负责管理所有客户端连接，提供添加、删除、查找客户端等功能
    """
    
    def __init__(self):
        self.clients: Dict[str, Client] = {}  # 用户名 -> Client对象
    
    def add_client(self, username: str, client_socket: socket.socket, address: tuple) -> bool:
        """
        添加客户端
        
        Args:
            username: 用户名
            client_socket: 客户端套接字
            address: 客户端地址
            
        Returns:
            bool: 添加成功返回True，如果用户已存在返回False
        """
        if username in self.clients:
            return False
            
        client = Client(username, client_socket, address)
        self.clients[username] = client
        return True
    
    def remove_client(self, username: str) -> bool:
        """
        移除客户端
        
        Args:
            username: 用户名
            
        Returns:
            bool: 移除成功返回True，如果用户不存在返回False
        """
        if username not in self.clients:
            return False
            
        client = self.clients[username]
        client.disconnect()
        del self.clients[username]
        return True
    
    def get_client(self, username: str) -> Client:
        """
        获取客户端对象
        
        Args:
            username: 用户名
            
        Returns:
            Client: 客户端对象，如果用户不存在返回None
        """
        return self.clients.get(username)
    
    def get_all_usernames(self) -> List[str]:
        """
        获取所有用户名列表
        
        Returns:
            List[str]: 所有用户名列表
        """
        return list(self.clients.keys())
    
    def get_client_socket(self, username: str) -> socket.socket:
        """
        获取客户端套接字
        
        Args:
            username: 用户名
            
        Returns:
            socket.socket: 客户端套接字，如果用户不存在返回None
        """
        client = self.clients.get(username)
        return client.socket if client else None
    
    def client_exists(self, username: str) -> bool:
        """
        检查客户端是否存在
        
        Args:
            username: 用户名
            
        Returns:
            bool: 存在返回True，否则返回False
        """
        return username in self.clients