#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理器
处理文件相关请求
"""

import logging
from typing import Dict, Any
from server.managers.connection_manager import ConnectionManager
from common.log import server_log as log


class FileHandler:
    """文件处理器 - 处理所有文件相关的请求"""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    async def handle_file(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理文件请求"""
        username = request_data.get('username')
        filename = request_data.get('filename', '')
        file_data = request_data.get('data', '')
        file_size = request_data.get('size', 0)
        content_type = request_data.get('type', 'file')  # 默认为'file'类型
        
        # 确保file_size是整数类型
        if isinstance(file_size, str):
            try:
                file_size = int(file_size)
            except ValueError:
                file_size = 0

        if not username or not self.connection_manager.is_client_connected(username):
            return {
                'type': 'error',
                'success': False,
                'message': '用户未登录'
            }

        if not filename or not file_data:
            return {
                'type': 'error',
                'success': False,
                'message': '文件名和数据不能为空'
            }

        try:
            # 广播文件消息
            await self.connection_manager.message_manager.broadcast_file(
                username=username,
                filename=filename,
                file_data=file_data,
                file_size=file_size,
                content_type=content_type
            )

            return {
                'type': 'file_sent',
                'success': True,
                'message': '文件发送成功'
            }

        except Exception as e:
            log.error(f"文件处理失败: {e}")
            return {
                'type': 'error',
                'success': False,
                'message': '文件发送失败'
            }