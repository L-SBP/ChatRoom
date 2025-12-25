#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息管理器
负责消息的广播、存储和分发
"""

import json
import time
from typing import List, Optional
import socket

from sqlalchemy import select
from common.log import log
from common.database.pg_helper import PgHelper
from common.database.crud.global_messages_crud import GlobalMessageCRUD
from common.database.crud.users_crud import user_crud
from common.database.models.users import Users


class MessageManager:
    """消息管理器 - 负责所有消息的管理和分发"""

    def __init__(self, connection_manager, db_engine):
        self.connection_manager = connection_manager
        self.db_engine = db_engine
        self.message_crud = GlobalMessageCRUD()

    async def broadcast_message(self, username: str, message: str, timestamp=None, sender_socket=None) -> None:
        """广播文本消息"""
        if timestamp is None:
            timestamp = time.time()

        # 构造消息
        broadcast_message = {
            'type': 'text',
            'username': username,
            'content': message,
            'timestamp': time.strftime('%H:%M:%S', time.localtime(timestamp))
        }

        # 保存到数据库
        await self._save_text_message_to_db(username, message, timestamp)

        # 发送给所有客户端（除了发送者）
        await self._broadcast_to_clients(broadcast_message, exclude_socket=sender_socket)

    async def broadcast_file(self, username: str, filename: str,
                             file_data: str, file_size: int, sender_socket=None) -> None:
        """广播文件"""
        # 构造文件消息
        file_message = {
            'type': 'file',
            'username': username,
            'filename': filename,
            'data': file_data,
            'size': file_size
        }

        # 保存到数据库
        await self._save_file_message_to_db(username, filename, file_size, time.time())

        # 发送给所有客户端（除了发送者）
        await self._broadcast_to_clients(file_message, exclude_socket=sender_socket)

    async def broadcast_system_message(self, message: str) -> None:
        """广播系统消息"""
        broadcast_message = {
            'type': 'system',
            'message': message,
            'timestamp': time.strftime('%H:%M:%S', time.localtime())
        }

        # 保存到数据库
        await self._save_system_message_to_db(message, time.time())

        # 发送给所有客户端
        await self._broadcast_to_clients(broadcast_message)

    async def send_user_list(self) -> None:
        """发送用户列表给所有客户端"""
        users = self.connection_manager.get_all_usernames()

        user_list_message = {
            'type': 'user_list',
            'users': users
        }

        await self._broadcast_to_clients(user_list_message)

    async def send_user_list_to_client(self, client_socket: socket.socket) -> None:
        """发送用户列表给指定客户端"""
        users = self.connection_manager.get_all_usernames()

        user_list_message = {
            'type': 'user_list',
            'users': users
        }

        try:
            client_socket.send(json.dumps(user_list_message).encode('utf-8'))
        except Exception as e:
            log.error(f"发送用户列表失败: {e}")

    async def _broadcast_to_clients(self, message: dict, exclude_socket=None) -> None:
        """广播消息给所有客户端"""
        disconnected_clients: List[str] = []

        for username, client in self.connection_manager.clients.items():
            # 如果指定了排除的socket，则跳过该客户端
            if exclude_socket and client.socket == exclude_socket:
                continue
            
            try:
                client.socket.send(json.dumps(message).encode('utf-8'))
            except Exception as e:
                log.error(f"发送消息给用户 {username} 失败: {e}")
                disconnected_clients.append(username)

        # 清理断开连接的客户端
        for username in disconnected_clients:
            self.connection_manager.unregister_client(username)

    async def _save_text_message_to_db(self, username: Optional[str], content: str, timestamp: float) -> None:
        """保存文本消息到数据库"""
        try:
            async with PgHelper.get_async_session(self.db_engine) as session:
                user_id = None
                if username:
                    user = await user_crud.get_by_username(session, username)
                    user_id = user.user_id if user else None

                message_data = {
                    'user_id': user_id,
                    'content_type': 'text',
                    'content': content,
                    'file_size': 0,
                    'metadata_': {'timestamp': timestamp}
                }

                await self.message_crud.create(session, **message_data)
                log.debug(f"文本消息已保存到数据库: {username} - {content}")

        except Exception as e:
            log.error(f"保存文本消息到数据库失败: {e}")

    async def _save_file_message_to_db(self, username: Optional[str], filename: str, 
                                       file_size: int, timestamp: float) -> None:
        """保存文件消息到数据库"""
        try:
            async with PgHelper.get_async_session(self.db_engine) as session:
                user_id = None
                if username:
                    user = await user_crud.get_by_username(session, username)
                    user_id = user.user_id if user else None

                message_data = {
                    'user_id': user_id,
                    'content_type': 'file',
                    'content': filename,
                    'file_name': filename,
                    'file_size': file_size,
                    'metadata_': {'timestamp': timestamp}
                }

                await self.message_crud.create(session, **message_data)
                log.debug(f"文件消息已保存到数据库: {username} - {filename}")

        except Exception as e:
            log.error(f"保存文件消息到数据库失败: {e}")

    async def _save_image_message_to_db(self, username: Optional[str], filename: str, 
                                        file_size: int, timestamp: float) -> None:
        """保存图片消息到数据库"""
        try:
            async with PgHelper.get_async_session(self.db_engine) as session:
                user_id = None
                if username:
                    user = await user_crud.get_by_username(session, username)
                    user_id = user.user_id if user else None

                message_data = {
                    'user_id': user_id,
                    'content_type': 'image',
                    'content': filename,
                    'file_name': filename,
                    'file_size': file_size,
                    'metadata_': {'timestamp': timestamp}
                }

                await self.message_crud.create(session, **message_data)
                log.debug(f"图片消息已保存到数据库: {username} - {filename}")

        except Exception as e:
            log.error(f"保存图片消息到数据库失败: {e}")

    async def _save_video_message_to_db(self, username: Optional[str], filename: str, 
                                        file_size: int, timestamp: float) -> None:
        """保存视频消息到数据库"""
        try:
            async with PgHelper.get_async_session(self.db_engine) as session:
                user_id = None
                if username:
                    user = await user_crud.get_by_username(session, username)
                    user_id = user.user_id if user else None

                message_data = {
                    'user_id': user_id,
                    'content_type': 'video',
                    'content': filename,
                    'file_name': filename,
                    'file_size': file_size,
                    'metadata_': {'timestamp': timestamp}
                }

                await self.message_crud.create(session, **message_data)
                log.debug(f"视频消息已保存到数据库: {username} - {filename}")

        except Exception as e:
            log.error(f"保存视频消息到数据库失败: {e}")

    async def _save_audio_message_to_db(self, username: Optional[str], filename: str, 
                                        file_size: int, timestamp: float) -> None:
        """保存音频消息到数据库"""
        try:
            async with PgHelper.get_async_session(self.db_engine) as session:
                user_id = None
                if username:
                    user = await user_crud.get_by_username(session, username)
                    user_id = user.user_id if user else None

                message_data = {
                    'user_id': user_id,
                    'content_type': 'audio',
                    'content': filename,
                    'file_name': filename,
                    'file_size': file_size,
                    'metadata_': {'timestamp': timestamp}
                }

                await self.message_crud.create(session, **message_data)
                log.debug(f"音频消息已保存到数据库: {username} - {filename}")

        except Exception as e:
            log.error(f"保存音频消息到数据库失败: {e}")

    async def _save_system_message_to_db(self, content: str, timestamp: float) -> None:
        """保存系统消息到数据库"""
        try:
            async with PgHelper.get_async_session(self.db_engine) as session:
                message_data = {
                    'user_id': None,  # 系统消息没有特定用户
                    'content_type': 'system',
                    'content': content,
                    'file_size': 0,  # 添加file_size字段
                    'metadata_': {'timestamp': timestamp, 'is_system': True}
                }

                await self.message_crud.create(session, **message_data)
                log.debug(f"系统消息已保存到数据库: {content}")

        except Exception as e:
            log.error(f"保存系统消息到数据库失败: {e}")

    async def get_history_messages(self, message_id: str = None, limit: int = 50) -> list:
        """获取历史消息"""
        try:
            async with PgHelper.get_async_session(self.db_engine) as session:
                if message_id is None:
                    # 获取最新的limit条消息
                    messages = await self.message_crud.get_lasted_message(session, limit)
                else:
                    # 获取message_id之前的limit条消息
                    messages = await self.message_crud.get_before_message(session, message_id, limit)
                
                # 转换为客户端需要的格式
                history_messages = []
                for msg in messages:
                    # 获取用户名
                    username = "系统" if msg.user_id is None else "未知用户"
                    if msg.user_id:
                        # 使用get_by_id方法获取用户，如果不存在则返回None
                        query = select(Users).where(Users.user_id == msg.user_id)
                        user_result = await session.execute(query)
                        user = user_result.scalar_one_or_none()
                        if user:
                            username = user.username
                    
                    # 格式化消息
                    message_data = {
                        'message_id': str(msg.message_id),  # 确保UUID转为字符串
                        'username': username,
                        'content_type': msg.content_type,
                        'content': msg.content,
                        'timestamp': msg.created_at.isoformat(),  # 使用ISO格式时间戳
                        'file_size': msg.file_size,
                        'file_name': msg.file_name
                    }
                    history_messages.append(message_data)
                
                # 不需要反转，因为我们要按时间顺序（从旧到新）返回
                # history_messages.reverse()
                return history_messages
                
        except Exception as e:
            log.error(f"获取历史消息失败: {e}")
            return []
