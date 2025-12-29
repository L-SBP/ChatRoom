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

    async def handle_message(self, request_data: Dict[str, Any], client_socket=None) -> Dict[str, Any]:
        """处理消息请求（支持多种消息类型）"""
        username = request_data.get('username')
        content_type = request_data.get('content_type', 'text')
        content = request_data.get('content', '')
        timestamp = request_data.get('timestamp', time.time())

        # 检查是否为私聊消息
        message_type = request_data.get('message_type', 'public')
        if message_type == 'private':
            # 处理私聊消息
            receiver = request_data.get('receiver')
            if not receiver:
                return {
                    'type': 'error',
                    'success': False,
                    'message': '私聊消息必须指定接收者'
                }

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

            # 检查接收者是否在线
            if not self.connection_manager.is_client_connected(receiver):
                return {
                    'type': 'error',
                    'success': False,
                    'message': f'用户 {receiver} 不在线'
                }

            try:
                # 获取file_size并确保是整数类型
                file_size = request_data.get('size', 0)
                if isinstance(file_size, str):
                    try:
                        file_size = int(file_size)
                    except ValueError:
                        file_size = 0
                
                # 发送私聊消息
                success = await self.connection_manager.message_manager.send_private_message(
                    sender_username=username,
                    receiver_username=receiver,
                    content=content,
                    content_type=content_type,
                    timestamp=timestamp,
                    file_data=request_data.get('data', ''),
                    filename=request_data.get('filename', ''),
                    file_size=file_size
                )

                if success:
                    return {
                        'type': 'private_message_sent',
                        'success': True,
                        'message': '私聊消息发送成功'
                    }
                else:
                    return {
                        'type': 'error',
                        'success': False,
                        'message': '私聊消息发送失败'
                    }

            except Exception as e:
                log.error(f"私聊消息处理失败: {e}")
                return {
                    'type': 'error',
                    'success': False,
                    'message': '私聊消息发送失败'
                }

        # 处理普通消息（公共消息）
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
                    timestamp=timestamp,
                    sender_socket=client_socket
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
                    file_size=file_size,
                    sender_socket=client_socket,
                    content_type=content_type
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
    
    async def handle_get_private_history(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取私聊历史消息的请求"""
        try:
            conversation_id = request_data.get('conversation_id')
            limit = request_data.get('limit', 50)
            
            if not conversation_id:
                return {
                    'type': 'error',
                    'success': False,
                    'message': '会话ID不能为空'
                }
            
            # 获取私聊历史消息
            history_messages = await self.connection_manager.message_manager.get_private_history_messages(conversation_id, limit)
            
            return {
                'type': 'private_history',
                'success': True,
                'messages': history_messages
            }
            
        except Exception as e:
            log.error(f"获取私聊历史消息失败: {e}")
            return {
                'type': 'error',
                'success': False,
                'message': '获取私聊历史消息失败'
            }