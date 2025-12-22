#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端处理器
处理单个客户端的整个生命周期
"""

import json
import socket
import asyncio
import logging
from typing import Dict, Any, Optional

from common.log import log
from server.models.client import Client


class ClientHandler:
    """客户端处理器 - 每个客户端连接对应一个实例"""

    def __init__(self, client_socket: socket.socket, client_address: tuple,
                 connection_manager):
        self.client_socket = client_socket
        self.client_address = client_address
        self.connection_manager = connection_manager
        self.username: Optional[str] = None
        self.authenticated = False

    async def handle_client(self) -> None:
        """处理客户端连接"""
        try:
            # 处理认证阶段
            await self._handle_authentication()

            # 处理已认证的消息
            if self.authenticated and self.username:
                await self._handle_messages()

        except (ConnectionError, asyncio.CancelledError) as e:
            log.info(f"客户端 {self.client_address} 断开连接: {e}")
        except Exception as e:
            log.error(f"处理客户端 {self.client_address} 时出错: {e}")
        finally:
            await self._cleanup()

    async def _handle_authentication(self) -> None:
        """处理客户端认证"""
        try:
            loop = asyncio.get_event_loop()

            # 接收认证请求
            data = await loop.sock_recv(self.client_socket, 1024)
            if not data:
                return

            # 解析请求
            request = json.loads(data.decode('utf-8'))
            request_type = request.get('type')

            # 处理不同类型的请求
            if request_type == 'login':
                response = await self._handle_login(request)
            elif request_type == 'register':
                response = await self._handle_register(request)
            else:
                response = {
                    'type': 'error',
                    'success': False,
                    'message': f'未知的请求类型: {request_type}'
                }

            # 发送响应
            await self._send_response(response)

        except json.JSONDecodeError:
            log.warning(f"客户端 {self.client_address} 发送的数据格式错误")
            await self._send_error("无效的消息格式")
        except Exception as e:
            log.error(f"认证处理失败: {e}")
            await self._send_error("认证失败")

    async def _handle_login(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理登录请求"""
        username = request.get('username')
        password = request.get('password')

        if not username or not password:
            return {
                'type': 'login_failed',
                'success': False,
                'message': '用户名和密码不能为空'
            }

        # 验证用户身份
        auth_result = await self.connection_manager.auth_manager.authenticate(
            username=username,
            password=password
        )

        if auth_result:
            # 创建客户端对象
            client = Client(username, self.client_socket, self.client_address)

            # 注册客户端
            if self.connection_manager.register_client(username, client):
                # 广播用户加入消息
                await self.connection_manager.broadcast_system_message(
                    f"{username} 加入了聊天室"
                )
                
                # 发送用户列表给所有客户端（包括刚连接的客户端）
                await self.connection_manager.send_user_list()

                log.info(f"用户 {username} 登录成功")
                self.authenticated = True
                self.username = username

                return {
                    'type': 'login_success',
                    'success': True,
                    'message': '登录成功',
                    'username': username
                }
            else:
                return {
                    'type': 'login_failed',
                    'success': False,
                    'message': '用户已在线'
                }
        else:
            return {
                'type': 'login_failed',
                'success': False,
                'message': '用户名或密码错误'
            }

    async def _handle_register(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理注册请求"""
        username = request.get('username')
        password = request.get('password')
        email = request.get('email', '')
        display_name = request.get('display_name', username)

        if not username or not password:
            return {
                'type': 'register_failed',
                'success': False,
                'message': '用户名和密码不能为空'
            }

        # 注册用户
        register_result = await self.connection_manager.auth_manager.register(
            username=username,
            password=password,
            email=email,
            display_name=display_name
        )

        if register_result:
            log.info(f"用户 {username} 注册成功")
            return {
                'type': 'register_success',
                'success': True,
                'message': '注册成功'
            }
        else:
            return {
                'type': 'register_failed',
                'success': False,
                'message': '注册失败，用户名可能已存在'
            }

    async def _handle_messages(self) -> None:
        """处理已认证客户端的消息"""
        loop = asyncio.get_event_loop()

        while True:
            try:
                # 接收消息
                data = await loop.sock_recv(self.client_socket, 1024)
                if not data:
                    break

                # 解析消息
                decoded_data = data.decode('utf-8').strip()
                if not decoded_data:
                    continue

                request = json.loads(decoded_data)
                request['username'] = self.username
                request_type = request.get('type')

                # 处理消息
                if request_type == 'message':
                    await self._process_message(request)
                elif request_type == 'file':
                    await self._process_file(request)
                elif request_type == 'refresh_users':
                    await self.connection_manager.message_manager.send_user_list_to_client(
                        self.client_socket
                    )
                elif request_type == 'logout':
                    break  # 退出循环，触发清理
                else:
                    await self._send_response({
                        'type': 'error',
                        'success': False,
                        'message': f'未知的消息类型: {request_type}'
                    })

            except json.JSONDecodeError:
                log.warning(f"客户端 {self.client_address} 发送的数据格式错误")
            except ConnectionResetError:
                break
            except Exception as e:
                log.error(f"处理消息时出错: {e}")
                break

    async def _process_message(self, request: Dict[str, Any]) -> None:
        """处理文本消息"""
        message = request.get('message', '')
        timestamp = request.get('timestamp')

        if message.strip():
            await self.connection_manager.message_manager.broadcast_message(
                username=self.username,
                message=message,
                timestamp=timestamp
            )

    async def _process_file(self, request: Dict[str, Any]) -> None:
        """处理文件"""
        filename = request.get('filename', '')
        file_data = request.get('data', '')
        # 确保file_size是整数类型
        file_size = request.get('size', 0)
        if isinstance(file_size, str):
            try:
                file_size = int(file_size)
            except ValueError:
                file_size = 0

        if filename and file_data:
            await self.connection_manager.message_manager.broadcast_file(
                username=self.username,
                filename=filename,
                file_data=file_data,
                file_size=file_size  # 确保传递的是整数
            )

    async def _send_response(self, response: Dict[str, Any]) -> None:
        """发送响应给客户端"""
        try:
            self.client_socket.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            log.error(f"发送响应失败: {e}")

    async def _send_error(self, message: str) -> None:
        """发送错误响应"""
        error_response = {
            'type': 'error',
            'success': False,
            'message': message
        }
        await self._send_response(error_response)

    async def _cleanup(self) -> None:
        """清理资源"""
        if self.username and self.connection_manager.is_client_connected(self.username):
            self.connection_manager.unregister_client(self.username)

            # 广播用户离开消息
            await self.connection_manager.broadcast_system_message(
                f"{self.username} 离开了聊天室"
            )

        # 关闭socket
        try:
            self.client_socket.close()
        except:
            pass
