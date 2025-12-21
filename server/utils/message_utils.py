#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息工具类
提供消息处理相关的通用工具函数
"""

import json
import logging

from server.models.client_manager import ClientManager


class MessageUtils:
    """
    消息工具类
    提供处理消息的通用方法
    """
    
    @staticmethod
    def send_message_to_client(client_socket, message: dict, logger: logging.Logger = None) -> bool:
        """
        发送消息到指定客户端
        
        Args:
            client_socket: 客户端套接字
            message: 消息字典
            logger: 日志记录器（可选）
            
        Returns:
            bool: 发送成功返回True，失败返回False
        """
        try:
            client_socket.send(json.dumps(message).encode('utf-8'))
            return True
        except Exception as e:
            if logger:
                logger.error(f"发送消息失败: {e}")
            return False
    
    @staticmethod
    def send_error_response(client_socket, message: str, logger: logging.Logger = None) -> bool:
        """
        发送错误响应
        
        Args:
            client_socket: 客户端套接字
            message: 错误消息
            logger: 日志记录器（可选）
            
        Returns:
            bool: 发送成功返回True，失败返回False
        """
        error_response = {
            'type': 'error',
            'message': message
        }
        return MessageUtils.send_message_to_client(client_socket, error_response, logger)