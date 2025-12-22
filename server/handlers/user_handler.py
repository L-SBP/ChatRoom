#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户处理器
处理用户相关请求
"""

import logging
from typing import Dict, Any
from server.managers.connection_manager import ConnectionManager
from common.log import log


class UserHandler:
    """用户处理器 - 处理所有用户相关的请求"""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    async def handle_refresh_users(self, request_data: Dict[str, Any],
                                   client_socket=None, client_address=None) -> Dict[str, Any]:
        """处理刷新用户列表请求"""
        try:
            # 发送用户列表给请求的客户端
            await self.connection_manager.message_manager.send_user_list_to_client(
                client_socket
            )

            return {
                'type': 'refresh_users_success',
                'success': True,
                'message': '用户列表已刷新'
            }

        except Exception as e:
            log.error(f"刷新用户列表失败: {e}")
            return {
                'type': 'error',
                'success': False,
                'message': '刷新用户列表失败'
            }