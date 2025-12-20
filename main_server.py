#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天室服务器启动脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server.chat_server import ChatServer
from common.config.config import config


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='聊天室服务器启动脚本')
    parser.add_argument('--host', default='0.0.0.0', help='服务器监听地址')
    parser.add_argument('--port', type=int, default=8888, help='服务器监听端口')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("         欢迎使用聊天室服务器")
    print("=" * 60)
    print(f"服务器地址: {args.host}")
    print(f"服务器端口: {args.port}")
    print("=" * 60)
    print("提示:")
    print("1. 服务器默认监听所有网络接口 (0.0.0.0)")
    print("2. 客户端可以通过局域网IP连接到此服务器")
    print("3. 按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    # 使用配置文件中的默认值
    host = args.host if args.host != '0.0.0.0' else config.server.host
    port = args.port if args.port != 8888 else config.server.port
    
    # 启动服务器
    server = ChatServer(host, port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        server.stop()
        print("服务器已停止")
    except Exception as e:
        print(f"服务器运行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
