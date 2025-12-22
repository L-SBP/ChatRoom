#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连接管理器
管理所有客户端连接，提供客户端注册、注销和查找功能
"""

import asyncio
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from server.models.client import Client
    from server.managers.message_manager import MessageManager
    from server.managers.auth_manager import AuthManager

from server.models.client import Client


class ConnectionManager:
    """连接管理器 - 负责客户端连接的生命周期管理"""

    def __init__(self):
        self.clients: Dict[str, Client] = {}  # 用户名 -> Client对象
        self.message_manager: Optional['MessageManager'] = None
        self.auth_manager: Optional['AuthManager'] = None
        self.db_engine = None

    async def initialize(self, db_engine) -> None:
        """初始化管理器"""
        self.db_engine = db_engine
        from server.managers.message_manager import MessageManager
        from server.managers.auth_manager import AuthManager

        self.message_manager = MessageManager(self, db_engine)
        self.auth_manager = AuthManager(db_engine)

    def register_client(self, username: str, client: 'Client') -> bool:
        """注册客户端"""
        if username in self.clients:
            return False

        self.clients[username] = client
        return True

    def unregister_client(self, username: str) -> bool:
        """注销客户端"""
        if username not in self.clients:
            return False

        client = self.clients[username]
        client.disconnect()
        del self.clients[username]
        return True

    def get_client(self, username: str) -> Optional['Client']:
        """获取客户端"""
        return self.clients.get(username)

    def get_all_usernames(self) -> List[str]:
        """获取所有用户名"""
        return list(self.clients.keys())

    def is_client_connected(self, username: str) -> bool:
        """检查客户端是否连接"""
        return username in self.clients

    async def broadcast_system_message(self, message: str) -> None:
        """广播系统消息"""
        if self.message_manager:
            await self.message_manager.broadcast_system_message(message)

    async def send_user_list(self) -> None:
        """发送用户列表给所有客户端"""
        if self.message_manager:
            await self.message_manager.send_user_list()

    async def cleanup(self) -> None:
        """清理所有连接"""
        for username in list(self.clients.keys()):
            self.unregister_client(username)