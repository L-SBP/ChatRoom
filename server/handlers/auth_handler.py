#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证处理器
处理用户登录、注册、注销等认证相关请求
"""

import json
import socket
import logging
from typing import Dict, Any

from common.log import log
from server.models.client import Client
from server.managers.connection_manager import ConnectionManager


class AuthHandler:
    """认证处理器 - 处理所有认证相关的请求"""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    async def handle_login(self, request_data: Dict[str, Any],
                           client_socket: socket.socket, client_address: tuple) -> Dict[str, Any]:
        """处理登录请求"""
        username = request_data.get('username')
        password = request_data.get('password')

        if not username or not password:
            return {
                'type': 'login_failed',
                'success': False,
                'message': '用户名和密码不能为空'
            }

        try:
            # 调用认证管理器验证用户
            auth_result = await self.connection_manager.auth_manager.authenticate(
                username=username,
                password=password
            )

            if auth_result:
                # 创建客户端对象
                client = Client(username, client_socket, client_address)

                # 注册客户端
                if self.connection_manager.register_client(username, client):
                    # 广播用户加入消息
                    await self.connection_manager.broadcast_system_message(
                        f"{username} 加入了聊天室"
                    )

                    # 发送用户列表给所有客户端
                    await self.connection_manager.send_user_list()

                    log.info(f"用户 {username} 登录成功")

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

        except Exception as e:
            log.error(f"登录处理失败: {e}")
            return {
                'type': 'login_failed',
                'success': False,
                'message': '登录失败，请稍后重试'
            }

    async def handle_register(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理注册请求"""
        username = request_data.get('username')
        password = request_data.get('password')
        email = request_data.get('email', '')
        display_name = request_data.get('display_name', username)

        if not username or not password:
            return {
                'type': 'register_failed',
                'success': False,
                'message': '用户名和密码不能为空'
            }

        try:
            # 调用认证管理器注册用户
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

        except Exception as e:
            log.error(f"注册处理失败: {e}")
            return {
                'type': 'register_failed',
                'success': False,
                'message': '注册失败，请稍后重试'
            }

    async def handle_logout(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理注销请求"""
        username = request_data.get('username')

        if username and self.connection_manager.is_client_connected(username):
            self.connection_manager.unregister_client(username)

            # 广播用户离开消息
            await self.connection_manager.broadcast_system_message(
                f"{username} 离开了聊天室"
            )

        return {
            'type': 'logout_success',
            'success': True,
            'message': '注销成功'
        }