# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# 消息控制器
# 处理各种类型的消息和客户端交互
# """
#
# import json
# import time
# import logging
# from typing import Dict, List
#
# from common.database.crud.users_crud import UsersCRUD
# from common.database.models import GlobalMessage, Users
# from common.database.pg_helper import PgHelper
# from server.models.client_manager import ClientManager
# from common.database.crud.global_messages_crud import GlobalMessageCRUD
#
#
# class MessageController:
#     """
#     消息控制器类
#     负责处理客户端发送的各种消息类型，包括文本消息、文件传输等
#     """
#
#     def __init__(self, client_manager: ClientManager, logger: logging.Logger, db_engine, users_crud: UsersCRUD):
#         self.client_manager = client_manager
#         self.logger = logger
#         self.db_engine = db_engine
#         self.message_crud = GlobalMessageCRUD()
#         self.users_crud = users_crud
#
#     async def broadcast_message(self, username: str, message: str, timestamp=None):
#         """
#         广播文本消息给所有客户端
#
#         Args:
#             username: 发送消息的用户名
#             message: 消息内容
#             timestamp: 时间戳（可选）
#         """
#         if timestamp is None:
#             timestamp = time.time()
#
#         # 构造消息
#         broadcast_message = {
#             'type': 'message',
#             'username': username,
#             'message': message,
#             'timestamp': time.strftime('%H:%M:%S', time.localtime(timestamp))
#         }
#
#         # 保存消息到数据库
#         try:
#             async with PgHelper.get_async_session(self.db_engine) as session:
#                 user_obj: Users = await self.users_crud.get_by_username(session, username)
#                 GlobalMessage(
#                     user_id=user_obj.user_id,
#                     content_type='text',
#                     content=message,
#                     metadata_={'timestamp': timestamp}
#                 )
#                 await session.add(GlobalMessage)
#                 await session.refresh(GlobalMessage)
#                 await session.commit()
#                 self.logger.info(f"消息已保存到数据库: {username} - {message}")
#
#             message_data = {
#                 'user_id': user_obj.user_id,
#                 'content_type': 'text',
#                 'content': message,
#                 'metadata_': {'timestamp': timestamp}
#             }
#
#             # 使用异步方式保存消息
#             import asyncio
#             loop = asyncio.get_event_loop()
#             loop.run_until_complete(
#                 self.message_crud.create(self.db_engine, **message_data)
#             )
#
#             self.logger.info(f"消息已保存到数据库: {username} - {message}")
#         except Exception as e:
#             self.logger.error(f"保存消息到数据库失败: {e}")
#
#         # 发送给所有客户端
#         disconnected_clients = []
#         for client_name, client in self.client_manager.clients.items():
#             try:
#                 client.socket.send(json.dumps(broadcast_message).encode('utf-8'))
#             except Exception as e:
#                 self.logger.error(f"发送消息给用户 {client_name} 失败: {e}")
#                 disconnected_clients.append(client_name)
#
#         # 移除断开连接的客户端
#         for client_name in disconnected_clients:
#             self.client_manager.remove_client(client_name)
#
#     def broadcast_file(self, username: str, filename: str, file_data: str, file_size: int):
#         """
#         广播文件给所有客户端
#
#         Args:
#             username: 发送文件的用户名
#             filename: 文件名
#             file_data: 文件数据
#             file_size: 文件大小
#         """
#         # 构造文件消息
#         file_message = {
#             'type': 'file',
#             'username': username,
#             'filename': filename,
#             'data': file_data,
#             'size': file_size
#         }
#
#         # 保存文件消息到数据库
#         try:
#             # 这里需要获取user_id，暂时使用username作为占位符
#             # 实际应用中应该从数据库查询user_id
#             user_id = username
#
#             file_message_data = {
#                 'user_id': user_id,
#                 'content_type': 'file',
#                 'content': filename,  # 文件名作为内容
#                 'file_name': filename,
#                 'file_size': str(file_size),
#                 'metadata_': {'file_data_length': len(file_data)}
#             }
#
#             # 使用异步方式保存文件消息
#             import asyncio
#             loop = asyncio.get_event_loop()
#             loop.run_until_complete(
#                 self.message_crud.create(self.db_engine, **file_message_data)
#             )
#
#             self.logger.info(f"文件消息已保存到数据库: {username} - {filename} ({file_size} bytes)")
#         except Exception as e:
#             self.logger.error(f"保存文件消息到数据库失败: {e}")
#
#         # 发送给所有客户端
#         disconnected_clients = []
#         for client_name, client in self.client_manager.clients.items():
#             try:
#                 client.socket.send(json.dumps(file_message).encode('utf-8'))
#             except Exception as e:
#                 self.logger.error(f"发送文件给用户 {client_name} 失败: {e}")
#                 disconnected_clients.append(client_name)
#
#         # 移除断开连接的客户端
#         for client_name in disconnected_clients:
#             self.client_manager.remove_client(client_name)
#
#     def broadcast_system_message(self, message: str):
#         """
#         广播系统消息
#
#         Args:
#             message: 系统消息内容
#         """
#         broadcast_message = {
#             'type': 'system',
#             'message': message,
#             'timestamp': time.strftime('%H:%M:%S', time.localtime())
#         }
#
#         # 保存系统消息到数据库
#         try:
#             # 系统消息的user_id可以设置为None或者一个特殊的系统用户ID
#             user_id = None  # 系统消息没有特定的用户
#
#             system_message_data = {
#                 'user_id': user_id,
#                 'content_type': 'system',
#                 'content': message,
#                 'metadata_': {'is_system': True}
#             }
#
#             # 使用异步方式保存系统消息
#             import asyncio
#             loop = asyncio.get_event_loop()
#             loop.run_until_complete(
#                 self.message_crud.create(self.db_engine, **system_message_data)
#             )
#
#             self.logger.info(f"系统消息已保存到数据库: {message}")
#         except Exception as e:
#             self.logger.error(f"保存系统消息到数据库失败: {e}")
#
#         # 发送给所有客户端
#         disconnected_clients = []
#         for client_name, client in self.client_manager.clients.items():
#             try:
#                 client.socket.send(json.dumps(broadcast_message).encode('utf-8'))
#             except Exception as e:
#                 self.logger.error(f"发送系统消息给用户 {client_name} 失败: {e}")
#                 disconnected_clients.append(client_name)
#
#         # 移除断开连接的客户端
#         for client_name in disconnected_clients:
#             self.client_manager.remove_client(client_name)
#
#     def send_user_list(self):
#         """发送用户列表给所有客户端"""
#         users = self.client_manager.get_all_usernames()
#
#         user_list_message = {
#             'type': 'user_list',
#             'users': users
#         }
#
#         disconnected_clients = []
#         for client_name, client in self.client_manager.clients.items():
#             try:
#                 client.socket.send(json.dumps(user_list_message).encode('utf-8'))
#             except Exception as e:
#                 self.logger.error(f"发送用户列表给用户 {client_name} 失败: {e}")
#                 disconnected_clients.append(client_name)
#
#         # 移除断开连接的客户端
#         for client_name in disconnected_clients:
#             self.client_manager.remove_client(client_name)
#
#     def send_user_list_to_client(self, client_socket):
#         """
#         发送用户列表给指定客户端
#
#         Args:
#             client_socket: 目标客户端套接字
#         """
#         users = self.client_manager.get_all_usernames()
#
#         user_list_message = {
#             'type': 'user_list',
#             'users': users
#         }
#
#         try:
#             client_socket.send(json.dumps(user_list_message).encode('utf-8'))
#         except Exception as e:
#             self.logger.error(f"发送用户列表失败: {e}")
