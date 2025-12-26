#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端模型
处理客户端连接信息和状态管理
"""

import socket
import time
from typing import Dict, Any
from common.log import server_log as log


class Client:
    """
    客户端模型类
    管理单个客户端的连接信息和状态
    """
    
    def __init__(self, username: str, client_socket: socket.socket, address: tuple):
        self.username = username
        self.socket = client_socket
        self.address = address
        self.login_time = time.time()
        
    def disconnect(self):
        """断开客户端连接"""
        try:
            self.socket.close()
        except:
            pass