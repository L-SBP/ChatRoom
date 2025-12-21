#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端控制器
处理客户端连接和消息分发逻辑
"""

import json
import time
import logging
from typing import Tuple
import socket
import asyncio

from server.controllers.auth_controller import AuthController
from server.controllers.message_controller import MessageController
from server.models.client_manager import ClientManager
from server.utils.message_utils import MessageUtils
from server.utils.password_utils import password_utils
from common.database.pg_helper import PgHelper
from common.database.crud.users_crud import user_crud


class ClientController:
    """
    客户端控制器类
    负责处理客户端连接后的各种操作，包括登录、注册、消息处理等
    """
    
    def __init__(self, client_manager: ClientManager, message_controller: MessageController, 
                 logger: logging.Logger, db_engine):
        self.client_manager = client_manager
        self.message_controller = message_controller
        self.logger = logger
        self.auth_controller = AuthController()
        self.db_engine = db_engine
    
    async def handle_initial_connection(self, client_socket: socket.socket, address: Tuple[str, int]) -> str:
        """
        处理客户端初始连接，主要是登录过程
        
        Args:
            client_socket: 客户端套接字
            address: 客户端地址
            
        Returns:
            str: 登录成功的用户名，失败则返回None
        """
        try:
            # 使用asyncio的loop.sock_recv来接收数据
            loop = asyncio.get_event_loop()
            data = await loop.sock_recv(client_socket, 1024)
            if not data:
                return None
            
            # 解析JSON数据
            message = json.loads(data.decode('utf-8'))
            msg_type = message.get('type')
            
            if msg_type == 'login':
                # 处理登录
                username = message.get('username')
                password = message.get('password')
                
                if await self._authenticate_and_login(client_socket, username, password, address):
                    return username
                    
            elif msg_type == 'register':
                # 处理注册
                await self._handle_registration(client_socket, message, address)
                # 注册完成后关闭连接，客户端需要重新连接进行登录
                return None
                
            else:
                # 其他消息需要先登录
                MessageUtils.send_error_response(client_socket, '请先登录', self.logger)
                
        except json.JSONDecodeError:
            self.logger.warning(f"客户端 {address} 发送的数据格式错误")
        except Exception as e:
            self.logger.error(f"处理客户端 {address} 初始连接时出错: {e}")
            
        return None
    
    async def _handle_registration(self, client_socket: socket.socket, message: dict, address: Tuple[str, int]):
        """
        处理用户注册请求
        
        Args:
            client_socket: 客户端套接字
            message: 注册消息
            address: 客户端地址
        """
        try:
            username = message.get('username')
            password = message.get('password')
            email = message.get('email', '')
            display_name = message.get('display_name', username)
            
            # 修复：使用await关键字调用异步方法
            result = await self.auth_controller.register_user(self.db_engine, username, password, email, display_name)
            
            if result:
                response = {
                    'type': 'register_success',
                    'message': '注册成功'
                }
                MessageUtils.send_message_to_client(client_socket, response, self.logger)
                self.logger.info(f"用户 {username} 注册成功")
            else:
                response = {
                    'type': 'register_failed',
                    'message': '注册失败，请稍后重试'
                }
                MessageUtils.send_message_to_client(client_socket, response, self.logger)
                
        except Exception as e:
            self.logger.error(f"处理客户端 {address} 注册请求时出错: {e}")
            response = {
                'type': 'register_failed',
                'message': '服务器内部错误'
            }
            MessageUtils.send_message_to_client(client_socket, response, self.logger)
        finally:
            client_socket.close()
    
    async def _authenticate_and_login(self, client_socket: socket.socket, username: str, 
                               password: str, address: Tuple[str, int]) -> bool:
        """
        验证用户并处理登录逻辑
        
        Args:
            client_socket: 客户端套接字
            username: 用户名
            password: 密码
            address: 客户端地址
            
        Returns:
            bool: 登录是否成功
        """
        # 运行异步认证函数
        auth_result = await self.auth_controller.authenticate_user(self.db_engine, username, password)
        if auth_result:
            # 登录成功
            if self.client_manager.add_client(username, client_socket, address):
                response = {
                    'type': 'login_success',
                    'message': '登录成功',
                    'username': username
                }
                MessageUtils.send_message_to_client(client_socket, response, self.logger)
                
                # 发送用户列表
                self.message_controller.send_user_list()
                
                # 发送欢迎消息
                self.message_controller.broadcast_system_message(f"{username} 加入了聊天室")
                self.logger.info(f"用户 {username} 登录成功")
                return True
        else:
            # 登录失败
            response = {
                'type': 'login_failed',
                'message': '用户名或密码错误'
            }
            MessageUtils.send_message_to_client(client_socket, response, self.logger)
            client_socket.close()
            return False
    
    async def handle_authenticated_messages(self, username: str, client_socket: socket.socket, 
                                     address: Tuple[str, int]):
        """
        处理已认证用户的消息
        
        Args:
            username: 用户名
            client_socket: 客户端套接字
            address: 客户端地址
            
        Returns:
            bool: True表示继续处理消息，False表示客户端已断开连接
        """
        try:
            # 使用asyncio的loop.sock_recv来接收数据
            loop = asyncio.get_event_loop()
            data = await loop.sock_recv(client_socket, 1024)
            if not data:
                self.client_manager.remove_client(username)
                return False  # 客户端已断开连接
            
            # 检查数据是否完整，避免解析错误
            decoded_data = data.decode('utf-8')
            if not decoded_data.strip():
                return True  # 空数据，继续处理后续消息
                
            message = json.loads(decoded_data)
            msg_type = message.get('type')
            
            if msg_type == 'message':
                # 处理普通消息
                self._handle_message(username, message)
            
            elif msg_type == 'file':
                # 处理文件
                self._handle_file(username, message)
            
            elif msg_type == 'refresh_users':
                # 刷新用户列表
                self.message_controller.send_user_list_to_client(client_socket)
            
            elif msg_type == 'logout':
                # 处理退出
                self.client_manager.remove_client(username)
                return False  # 客户端主动退出
                
        except json.JSONDecodeError as e:
            self.logger.warning(f"客户端 {address} 发送的数据格式错误: {e}")
        except ConnectionResetError:
            # 客户端断开连接
            self.logger.info(f"客户端 {address} 断开连接")
            self.client_manager.remove_client(username)
            return False
        except OSError as e:
            # 处理套接字错误，比如WinError 10038
            self.logger.error(f"处理客户端 {address} 消息时出现套接字错误: {e}")
            self.client_manager.remove_client(username)
            return False
        except Exception as e:
            self.logger.error(f"处理客户端 {address} 消息时出错: {e}")
            # 遇到未知错误时也断开连接
            self.client_manager.remove_client(username)
            return False
            
        return True  # 继续处理消息
    
    def _handle_message(self, username: str, message: dict):
        """
        处理文本消息
        
        Args:
            username: 用户名
            message: 消息字典
        """
        if not username or not self.client_manager.client_exists(username):
            return
        
        # 获取消息内容
        msg_content = message.get('message', '')
        timestamp = message.get('timestamp', time.time())
        
        if not msg_content:
            return
        
        # 广播消息给所有客户端
        self.message_controller.broadcast_message(username, msg_content, timestamp)
    
    def _handle_file(self, username: str, file_message: dict):
        """
        处理文件消息
        
        Args:
            username: 用户名
            file_message: 文件消息字典
        """
        if not username or not self.client_manager.client_exists(username):
            return
        
        # 获取文件信息
        filename = file_message.get('filename', '')
        file_data = file_message.get('data', '')
        file_size = file_message.get('size', 0)
        
        if not filename or not file_data:
            return
        
        # 广播文件给所有客户端
        self.message_controller.broadcast_file(username, filename, file_data, file_size)
        
        self.logger.info(f"用户 {username} 发送文件: {filename} ({file_size} bytes)")