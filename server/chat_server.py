#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天室服务器 - 重构版
负责启动服务器、接受连接、创建处理器，不处理具体业务逻辑
"""

import socket
import logging
import asyncio
from typing import Optional

from common.config.server.config import get_server_config
from common.database.pg_helper import PgHelper
from server.handlers.client_handler import ClientHandler
from server.managers.connection_manager import ConnectionManager
from common.log import log


class ChatServer:
    """聊天服务器类 - 重构版，单一职责：启动和监听"""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        # 获取配置
        self.config = get_server_config()

        # 设置主机和端口
        self.host = host or self.config.server.host or '0.0.0.0'
        self.port = port or self.config.server.port or 8888

        # 核心组件
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.db_engine = None

        # 管理器
        self.connection_manager = ConnectionManager()

    async def initialize(self) -> None:
        """初始化服务器组件"""
        try:
            # 初始化数据库引擎
            self.db_engine = PgHelper.get_async_engine()
            log.info("数据库引擎初始化成功")

            # 初始化连接管理器
            await self.connection_manager.initialize(self.db_engine)
            log.info("连接管理器初始化成功")

        except Exception as e:
            log.error(f"服务器初始化失败: {e}")
            raise

    async def start(self) -> None:
        """启动服务器"""
        try:
            # 初始化组件
            await self.initialize()

            # 创建服务器socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.setblocking(False)
            self.running = True

            log.info(f"服务器启动成功，监听地址: {self.host}:{self.port}")
            print(f"服务器启动成功，监听地址: {self.host}:{self.port}")
            print("等待客户端连接...")

            # 主事件循环
            await self._accept_connections()

        except Exception as e:
            log.error(f"服务器启动失败: {e}")
            raise
        finally:
            await self.stop()

    async def _accept_connections(self) -> None:
        """接受客户端连接"""
        loop = asyncio.get_event_loop()

        while self.running:
            try:
                # 异步接受连接
                client_socket, client_address = await loop.sock_accept(self.server_socket)
                client_socket.setblocking(True)

                log.info(f"新连接来自: {client_address}")

                # 为每个客户端创建独立的处理器
                client_handler = ClientHandler(
                    client_socket=client_socket,
                    client_address=client_address,
                    connection_manager=self.connection_manager
                )

                # 创建异步任务处理客户端
                asyncio.create_task(client_handler.handle_client())

            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.running:
                    log.error(f"接受连接时出错: {e}")

    async def stop(self) -> None:
        """停止服务器"""
        self.running = False

        # 关闭服务器socket
        if self.server_socket:
            self.server_socket.close()

        # 清理连接管理器
        if self.connection_manager:
            await self.connection_manager.cleanup()

        # 关闭数据库引擎
        if self.db_engine:
            await PgHelper.close_async_engine()

        log.info("服务器已停止")


async def main_async():
    """异步主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='聊天室服务器')
    parser.add_argument('--host', default=None, help='服务器监听地址')
    parser.add_argument('--port', type=int, default=None, help='服务器监听端口')

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
        await server.stop()


def main():
    """主函数"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()