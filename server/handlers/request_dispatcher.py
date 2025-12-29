#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
请求分发器
根据请求类型将请求分派到对应的处理器
"""

import json
import socket
import logging
from typing import Dict, Any, Optional
from server.handlers.auth_handler import AuthHandler
from server.handlers.message_handler import MessageHandler
from server.handlers.user_handler import UserHandler
from server.handlers.file_handler import FileHandler
from server.managers.connection_manager import ConnectionManager
from common.log import server_log as log


class RequestDispatcher:
    """请求分发器 - 负责路由请求到对应的处理器"""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

        # 初始化处理器
        self.auth_handler = AuthHandler(connection_manager)
        self.message_handler = MessageHandler(connection_manager)
        self.user_handler = UserHandler(connection_manager)
        self.file_handler = FileHandler(connection_manager)

        # 定义路由映射
        self.routes = {
            'login': self.auth_handler.handle_login,
            'register': self.auth_handler.handle_register,
            'text': self.message_handler.handle_message,
            'image': self.message_handler.handle_message,
            'video': self.message_handler.handle_message,
            'file': self.message_handler.handle_message,
            'audio': self.message_handler.handle_message,
            'private': self.message_handler.handle_message,  # 添加私聊消息路由
            'refresh_users': self.user_handler.handle_refresh_users,
            'logout': self.auth_handler.handle_logout,
            'get_history': self.message_handler.handle_get_history,
            'get_private_history': self.message_handler.handle_get_private_history,
        }

    async def dispatch(self, request_type: str, request_data: Dict[str, Any],
                       client_socket: socket.socket, client_address: tuple) -> Optional[Dict[str, Any]]:
        """分发请求到对应的处理器"""
        try:
            # 查找对应的处理器
            handler = self.routes.get(request_type)

            if handler:
                # 调用处理器
                # 检查处理器是否需要 client_socket 和 client_address 参数
                import inspect
                sig = inspect.signature(handler)
                handler_kwargs = {'request_data': request_data}
                
                if 'client_socket' in sig.parameters:
                    handler_kwargs['client_socket'] = client_socket
                if 'client_address' in sig.parameters:
                    handler_kwargs['client_address'] = client_address
                
                response = await handler(**handler_kwargs)
                return response
            else:
                # 未知请求类型
                return {
                    'type': 'error',
                    'success': False,
                    'message': f'未知的请求类型: {request_type}'
                }

        except Exception as e:
            log.error(f"请求分发失败: {e}")
            return {
                'type': 'error',
                'success': False,
                'message': '服务器内部错误'
            }