#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天室服务器
基于TCP协议的多客户端聊天服务器，使用异步IO提高性能
"""

import socket
import json
import time
import logging
import asyncio
from typing import Dict, List, Tuple, Set

# 导入配置
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入自定义模块
from server.models.client_manager import ClientManager
from server.controllers.message_controller import MessageController
from server.controllers.client_controller import ClientController
from server.utils.message_utils import MessageUtils

# 导入数据库模块
from common.database.pg_helper import PgHelper
from common.config.server.config import get_server_config

# 获取服务端配置
server_config = get_server_config()

class ChatServer:
    """聊天服务器类"""
    
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.client_manager = ClientManager()
        self.running = False
        self.server_socket = None
        self.db_engine = None
        
        # 使用配置中的主机和端口
        if server_config.server.host:
            self.host = server_config.server.host
        if server_config.server.port:
            self.port = server_config.server.port
            
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 初始化控制器
        self.message_controller = None
        self.client_controller = None
    
    async def start(self):
        """启动服务器"""
        try:
            # 创建数据库引擎
            self.db_engine = PgHelper.get_async_engine()
            
            # 初始化控制器
            self.message_controller = MessageController(self.client_manager, self.logger)
            self.client_controller = ClientController(self.client_manager, self.message_controller, self.logger, self.db_engine)
            
            # 创建服务器socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 绑定地址和端口
            self.server_socket.bind((self.host, self.port))
            
            # 开始监听
            self.server_socket.listen(5)
            self.server_socket.setblocking(False)  # 设置为非阻塞模式
            self.running = True
            
            self.logger.info(f"服务器启动成功，监听地址: {self.host}:{self.port}")
            print(f"服务器启动成功，监听地址: {self.host}:{self.port}")
            print("等待客户端连接...")
            
            # 使用asyncio处理客户端连接
            loop = asyncio.get_event_loop()
            while self.running:
                try:
                    # 使用loop.sock_accept异步接受连接
                    client_socket, client_address = await loop.sock_accept(self.server_socket)
                    client_socket.setblocking(True)  # 设置客户端socket为阻塞模式，避免处理复杂性
                    
                    self.logger.info(f"新连接来自: {client_address}")
                    
                    # 为每个客户端创建异步任务
                    asyncio.create_task(self.handle_client_async(client_socket, client_address))
                    
                except Exception as e:
                    if self.running:
                        self.logger.error(f"接受连接时出错: {e}")
                        
        except Exception as e:
            self.logger.error(f"服务器启动失败: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """停止服务器"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        
        if self.db_engine:
            await PgHelper.close_async_engine()
        
        self.logger.info("服务器已停止")
    
    async def handle_client_async(self, client_socket: socket.socket, address: Tuple[str, int]):
        """异步处理客户端连接"""
        username = None
        try:
            # 处理客户端初始连接和登录
            username = await self.client_controller.handle_initial_connection(client_socket, address)
            
            if username:
                # 处理已认证用户的消息
                while self.running:
                    try:
                        result = await self.client_controller.handle_authenticated_messages(username, client_socket, address)
                        # 如果处理结果为False，说明客户端已断开连接
                        if result is False:
                            break
                    except Exception as e:
                        self.logger.error(f"处理客户端 {address} 消息时出错: {e}")
                        break
        
        except Exception as e:
            self.logger.error(f"处理客户端 {address} 时出错: {e}")
        finally:
            if username and self.client_manager.client_exists(username):
                self.client_manager.remove_client(username)
            # 确保socket被关闭
            try:
                client_socket.close()
            except:
                pass


async def main_async():
    """异步主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='聊天室服务器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器监听地址')
    parser.add_argument('--port', type=int, default=8888, help='服务器监听端口')
    
    args = parser.parse_args()
    
    # 启动服务器
    server = ChatServer(args.host, args.port)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        await server.stop()
    except Exception as e:
        print(f"服务器运行出错: {e}")


def main():
    """主函数"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()