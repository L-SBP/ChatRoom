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
import os
from pathlib import Path
import datetime
import base64

from sqlalchemy import select
from common.log import server_log as log
from common.database.pg_helper import PgHelper
from common.database.crud.global_messages_crud import GlobalMessageCRUD
from common.database.crud.users_crud import user_crud
from common.database.crud.files_crud import FilesCRUD
from common.database.models.users import Users
from common.config.profile import Profile
from common.database.crud.private_messages_crud import PrivateMessageCRUD
from common.database.crud.private_conversations_crud import PrivateConversationCRUD


class MessageManager:
    """消息管理器 - 负责所有消息的管理和分发"""

    def __init__(self, connection_manager, db_engine):
        self.connection_manager = connection_manager
        self.db_engine = db_engine
        self.message_crud = GlobalMessageCRUD()
        self.file_crud = FilesCRUD()
        self.private_message_crud = PrivateMessageCRUD()
        self.private_conversation_crud = PrivateConversationCRUD()

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

    async def send_private_message(self, sender_username: str, receiver_username: str, content: str, 
                                 content_type: str = 'text', timestamp=None, file_data: str = None, 
                                 filename: str = None, file_size: int = 0) -> bool:
        """发送私聊消息"""
        if timestamp is None:
            timestamp = time.time()

        # 获取发送者和接收者信息
        async with PgHelper.get_async_session(self.db_engine) as session:
            sender = await user_crud.get_by_username(session, sender_username)
            receiver = await user_crud.get_by_username(session, receiver_username)
            
            if not sender or not receiver:
                log.error(f"发送私聊消息失败: 用户不存在 - {sender_username} -> {receiver_username}")
                return False

            # 获取或创建私聊会话
            conversation = await self.private_conversation_crud.get_by_users(
                session, str(sender.user_id), str(receiver.user_id)
            )
            if not conversation:
                # 创建新的私聊会话
                conversation = await self.private_conversation_crud.create(
                    session,
                    user1_id=min(str(sender.user_id), str(receiver.user_id)),
                    user2_id=max(str(sender.user_id), str(receiver.user_id))
                )

            # 构造私聊消息
            private_message = {
                'type': 'private',
                'message_type': 'private',
                'username': sender_username,
                'receiver': receiver_username,
                'content': content,
                'content_type': content_type,
                'timestamp': time.strftime('%H:%M:%S', time.localtime(timestamp))
            }

            # 如果是文件类型，添加文件相关信息
            if content_type in ['image', 'video', 'file', 'audio'] and filename:
                private_message.update({
                    'filename': filename,
                    'data': file_data,
                    'size': file_size
                })

            # 保存私聊消息到数据库
            message_data = {
                'conversation_id': str(conversation.conversation_id),
                'sender_id': str(sender.user_id),
                'receiver_id': str(receiver.user_id),
                'content_type': content_type,
                'content': content,
                'metadata_': {'timestamp': timestamp}
            }

            # 如果是文件类型，添加文件信息
            if content_type in ['image', 'video', 'file', 'audio'] and filename:
                message_data.update({
                    'file_name': filename,
                    'file_size': int(file_size) if file_size else 0
                })

            saved_message = await self.private_message_crud.create(session, **message_data)

            # 更新会话的最后消息信息
            await self.private_conversation_crud.update_last_message(
                session, str(conversation.conversation_id), str(saved_message.message_id)
            )

        # 检查接收者是否在线
        if self.connection_manager.is_client_connected(receiver_username):
            # 获取接收者的socket连接
            receiver_client = self.connection_manager.get_client(receiver_username)
            if receiver_client:
                try:
                    # 发送私聊消息给接收者
                    receiver_client.socket.send(json.dumps(private_message).encode('utf-8'))
                    log.info(f"私聊消息已发送给接收者: {sender_username} -> {receiver_username}")
                    
                    # 重要：不再回传给发送者，因为发送者已经有本地回显了
                    # 发送者可以通过发送成功后立即显示消息，不需要服务器回传
                    
                    return True
                except Exception as e:
                    log.error(f"发送私聊消息给 {receiver_username} 失败: {e}")
                    return False
            else:
                log.error(f"无法找到接收者 {receiver_username} 的客户端信息")
                return False
        else:
            log.info(f"接收者 {receiver_username} 不在线，消息已保存到数据库")
            return True  # 消息已保存到数据库，返回True表示处理成功

    async def broadcast_file(self, username: str, filename: str,
                             file_data: str, file_size: int, sender_socket=None, content_type: str = 'file') -> None:
        """广播文件"""
        log.debug(f"MessageManager.broadcast_file 开始广播文件: {filename}, 类型: {content_type}, 大小: {file_size} 字节, 发送者: {username}")
        
        # 保存文件到磁盘
        file_path, file_url = self._save_file_to_disk(username, filename, file_data)
        
        # 保存文件元数据到files表
        file_record = await self._save_file_metadata_to_db(username, filename, file_path, file_url, file_size, content_type)
        
        # 构造文件消息 - 包含file_data以便客户端直接保存
        file_message = {
            'type': content_type,
            'username': username,
            'content': filename,  # 添加content字段，客户端需要
            'filename': filename,
            'data': file_data,  # 包含文件数据以便客户端保存
            'size': file_size,
            'file_url': file_url,
            'file_id': str(file_record.file_id),
            'timestamp': time.time()  # 添加timestamp字段，客户端需要
        }

        # 保存到数据库 - 根据内容类型选择不同的保存方法
        log.debug(f"MessageManager.broadcast_file 保存{content_type}消息到数据库: {filename}")
        if content_type == 'image':
            await self._save_image_message_to_db(username, filename, file_size, time.time(), file_url=file_url, file_id=str(file_record.file_id))
        elif content_type == 'video':
            await self._save_video_message_to_db(username, filename, file_size, time.time(), file_url=file_url, file_id=str(file_record.file_id))
        elif content_type == 'audio':
            await self._save_audio_message_to_db(username, filename, file_size, time.time(), file_url=file_url, file_id=str(file_record.file_id))
        else:
            await self._save_file_message_to_db(username, filename, file_size, time.time(), file_url=file_url, file_id=str(file_record.file_id))

        # 发送给所有客户端（除了发送者）
        log.info(f"MessageManager.broadcast_file 准备广播{content_type}到所有客户端: {filename}")
        await self._broadcast_to_clients(file_message, exclude_socket=sender_socket)
        log.info(f"MessageManager.broadcast_file {content_type}广播完成: {filename}")

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
                                       file_size: int, timestamp: float, file_url: str = None, file_id: str = None) -> None:
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
                    'file_url': file_url,
                    'file_size': file_size,
                    'metadata_': {'timestamp': timestamp, 'file_id': file_id}
                }

                await self.message_crud.create(session, **message_data)
                log.debug(f"文件消息已保存到数据库: {username} - {filename}")

        except Exception as e:
            log.error(f"保存文件消息到数据库失败: {e}")

    async def _save_image_message_to_db(self, username: Optional[str], filename: str, 
                                        file_size: int, timestamp: float, file_url: str = None, file_id: str = None) -> None:
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
                    'file_url': file_url,
                    'file_size': file_size,
                    'metadata_': {'timestamp': timestamp, 'file_id': file_id}
                }

                await self.message_crud.create(session, **message_data)
                log.debug(f"图片消息已保存到数据库: {username} - {filename}")

        except Exception as e:
            log.error(f"保存图片消息到数据库失败: {e}")

    async def _save_video_message_to_db(self, username: Optional[str], filename: str, 
                                        file_size: int, timestamp: float, file_url: str = None, file_id: str = None) -> None:
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
                    'file_url': file_url,
                    'file_size': file_size,
                    'metadata_': {'timestamp': timestamp, 'file_id': file_id}
                }

                await self.message_crud.create(session, **message_data)
                log.debug(f"视频消息已保存到数据库: {username} - {filename}")

        except Exception as e:
            log.error(f"保存视频消息到数据库失败: {e}")

    async def _save_audio_message_to_db(self, username: Optional[str], filename: str, 
                                        file_size: int, timestamp: float, file_url: str = None, file_id: str = None) -> None:
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
                    'file_url': file_url,
                    'file_size': file_size,
                    'metadata_': {'timestamp': timestamp, 'file_id': file_id}
                }

                await self.message_crud.create(session, **message_data)
                log.debug(f"音频消息已保存到数据库: {username} - {filename}")

        except Exception as e:
            log.error(f"保存音频消息到数据库失败: {e}")

    async def _save_file_metadata_to_db(self, username: str, filename: str, file_path: str, file_url: str, file_size: int, content_type: str) -> object:
        """
        保存文件元数据到files表
        """
        try:
            async with PgHelper.get_async_session(self.db_engine) as session:
                # 获取用户ID
                user = await user_crud.get_by_username(session, username)
                user_id = user.user_id if user else None
                
                # 构造文件元数据
                file_metadata = {
                    'user_id': user_id,
                    'file_name': filename,
                    'file_path': file_path,
                    'file_url': file_url,
                    'file_type': content_type,
                    'file_size': int(file_size),  # 数据库中定义为bigint类型
                }
                
                # 保存到数据库
                file_record = await self.file_crud.create(session, **file_metadata)
                log.info(f"文件元数据已保存到数据库: {filename}")
                return file_record
        except Exception as e:
            log.error(f"保存文件元数据到数据库失败: {e}")
            raise

    def _save_file_to_disk(self, username: str, filename: str, file_data: str) -> tuple[str, str]:
        """
        将文件保存到磁盘，按用户隔离存储
        返回文件路径和文件URL
        """
        # 获取项目根目录
        project_root = Profile.get_project_root()
        
        # 创建按用户和日期组织的存储路径
        today = datetime.datetime.now()
        file_storage_path = project_root / "uploads" / username / f"{today.year}" / f"{today.month:02d}" / f"{today.day:02d}"
        
        # 确保目录存在
        file_storage_path.mkdir(parents=True, exist_ok=True)
        
        # 处理文件名冲突
        base_filename, ext = os.path.splitext(filename)
        final_filename = filename
        counter = 1
        while (file_storage_path / final_filename).exists():
            final_filename = f"{base_filename}_{counter}{ext}"
            counter += 1
        
        # 确保文件名是有效的（处理特殊字符）
        final_filename = final_filename.encode('utf-8', 'surrogateescape').decode('utf-8', 'surrogateescape')
        
        # 完整文件路径
        file_path = file_storage_path / final_filename
        
        # 解码文件数据并写入磁盘
        try:
            # 清理base64数据，移除可能的特殊字符（如换行符、空格等）
            # base64编码应该只包含字母、数字、+、/、=和可能的换行符
            cleaned_file_data = ''.join(c for c in file_data if c.isalnum() or c in '+/=')
            
            # 进行base64解码
            decoded_data = base64.b64decode(cleaned_file_data)
            with open(file_path, 'wb') as f:
                f.write(decoded_data)
            log.info(f"文件已保存到磁盘: {file_path}")
        except UnicodeDecodeError as e:
            log.error(f"文件数据包含非ASCII字符: {e}")
            raise
        except base64.binascii.Error as e:
            log.error(f"base64解码失败: {e}")
            log.error(f"原始数据长度: {len(file_data)}, 清理后数据长度: {len(cleaned_file_data)}")
            log.error(f"原始数据前100字符: {file_data[:100]}")
            raise
        except Exception as e:
            log.error(f"保存文件到磁盘失败: {e}")
            raise
        
        # 生成文件URL（相对路径）
        relative_path = file_path.relative_to(project_root)
        # 使用正斜杠并确保没有重复的/uploads前缀
        file_url = f"/{relative_path.as_posix()}"
        
        return str(file_path), file_url

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

    async def get_private_history_messages(self, conversation_id: str, limit: int = 50) -> List[dict]:
        """
        获取私聊历史消息
        """
        try:
            async with PgHelper.get_async_session(self.db_engine) as session:
                # 获取会话的所有消息
                messages = await self.private_message_crud.get_by_conversation_id(
                    session, conversation_id, limit=limit
                )
                
                history_messages = []
                for msg in messages:
                    # 获取发送者和接收者的用户名
                    sender = await user_crud.get_by_id(session, str(msg.sender_id))
                    receiver = await user_crud.get_by_id(session, str(msg.receiver_id))
                    
                    sender_name = sender.username if sender else "未知用户"
                    receiver_name = receiver.username if receiver else "未知用户"
                    
                    # 格式化消息
                    message_data = {
                        'message_id': str(msg.message_id),  # 确保UUID转为字符串
                        'conversation_id': str(msg.conversation_id),
                        'username': sender_name,
                        'receiver': receiver_name,
                        'content_type': msg.content_type,
                        'content': msg.content,
                        'timestamp': msg.created_at.isoformat(),  # 使用ISO格式时间戳
                        'file_size': msg.file_size,
                        'file_name': msg.file_name,
                        'is_read': msg.is_read
                    }
                    history_messages.append(message_data)
                
                # 按时间顺序返回（从旧到新）
                return history_messages
                
        except Exception as e:
            log.error(f"获取私聊历史消息失败: {e}")
            return []
