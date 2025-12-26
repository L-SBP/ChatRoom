#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息处理器
处理文本消息相关请求
"""

import time
from typing import Dict, Any
from server.managers.connection_manager import ConnectionManager
from common.log import server_log as log


class MessageHandler:
    """消息处理器 - 处理所有消息相关的请求"""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    async def handle_message(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理消息请求（支持多种消息类型）"""
        username = request_data.get('username')
        content_type = request_data.get('content_type', 'text')
        content = request_data.get('content', '')
        timestamp = request_data.get('timestamp', time.time())

        if not username or not self.connection_manager.is_client_connected(username):
            return {
                'type': 'error',
                'success': False,
                'message': '用户未登录'
            }

        if not content.strip():
            return {
                'type': 'error',
                'success': False,
                'message': '消息内容不能为空'
            }

        try:
            # 根据消息类型处理
            if content_type == 'text':
                # 广播文本消息
                await self.connection_manager.message_manager.broadcast_message(
                    username=username,
                    message=content,
                    timestamp=timestamp
                )
            elif content_type in ['image', 'video', 'file', 'audio']:
                # 广播文件消息
                file_data = request_data.get('data', '')
                file_size = request_data.get('size', 0)
                # 确保file_size是整数类型
                if isinstance(file_size, str):
                    try:
                        file_size = int(file_size)
                    except ValueError:
                        file_size = 0
                        
                filename = request_data.get('filename', '')
                
                await self.connection_manager.message_manager.broadcast_file(
                    username=username,
                    filename=filename,
                    file_data=file_data,
                    file_size=file_size
                )
            else:
                return {
                    'type': 'error',
                    'success': False,
                    'message': f'不支持的消息类型: {content_type}'
                }

            return {
                'type': 'message_sent',
                'success': True,
                'message': '消息发送成功'
            }

        except Exception as e:
            log.error(f"消息处理失败: {e}")
            return {
                'type': 'error',
                'success': False,
                'message': '消息发送失败'
            }

    async def handle_get_history(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取历史消息的请求"""
        try:
            message_id = request_data.get('message_id')
            limit = request_data.get('limit', 50)
            
            # 获取历史消息
            history_messages = await self.connection_manager.message_manager.get_history_messages(message_id, limit)
            
            return {
                'type': 'get_history',
                'success': True,
                'messages': history_messages
            }
            
        except Exception as e:
            log.error(f"获取历史消息失败: {e}")
            return {
                'type': 'error',
                'success': False,
                'message': '获取历史消息失败'
            }