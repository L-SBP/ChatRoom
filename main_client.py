#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天室客户端主入口（MVC架构版本）
基于PyQt5的GUI聊天应用程序
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import qdarkstyle

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from views.login_view import LoginView
from views.chat_view import ChatView
from views.register_view import RegisterView


class ChatRoomClient:
    """聊天室客户端主类（MVC架构）"""
    
    def __init__(self):
        self.app = None
        self.login_view = None
        self.chat_view = None
        self.register_view = None
        
    def run(self):
        """启动客户端"""
        # 创建应用
        self.app = QApplication(sys.argv)
        
        # 设置应用属性
        self.app.setApplicationName("聊天室客户端")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("HNU")
        self.app.setOrganizationDomain("hnu.edu.cn")
        
        # 设置样式
        self.app.setStyle("Fusion")
        
        # 应用深色主题
        self.app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        
        # 显示登录窗口
        self.show_login()
        
        # 运行应用
        sys.exit(self.app.exec_())
    
    def show_login(self):
        """显示登录视图"""
        self.login_view = LoginView()
        self.login_view.login_success.connect(self.on_login_success)
        self.login_view.show_register.connect(self.on_show_register)
        self.login_view.exit_app.connect(self.on_exit_app)
        self.login_view.show()
    
    def show_chat(self, username: str, server_host: str, server_port: int):
        """显示聊天视图"""
        self.chat_view = ChatView(server_host, server_port, username)
        self.chat_view.close_view.connect(self.on_chat_closed)
        self.chat_view.show()
    
    def show_register(self):
        """显示注册视图"""
        self.register_view = RegisterView()
        self.register_view.register_success.connect(self.on_register_success)
        self.register_view.show()
    
    def on_login_success(self, username: str):
        """处理登录成功"""
        # 获取服务器配置
        server_host = self.login_view.server_input.text().strip()
        server_port = self.login_view.port_input.text().strip()
        
        try:
            port_num = int(server_port)
        except ValueError:
            QMessageBox.warning(self.login_view, "错误", "端口号格式不正确")
            return
        
        # 隐藏登录窗口
        self.login_view.hide()
        
        # 显示聊天窗口
        self.show_chat(username, server_host, port_num)
    
    def on_show_register(self):
        """处理显示注册"""
        self.show_register()
    
    def on_exit_app(self):
        """处理退出应用"""
        self.app.quit()
    
    def on_register_success(self):
        """处理注册成功"""
        if self.register_view:
            self.register_view.hide()
        self.show_login()
    
    def on_chat_closed(self):
        """聊天窗口关闭时的处理"""
        # 重新显示登录窗口
        if self.login_view:
            self.login_view.show()


def main():
    """主函数"""
    try:
        client = ChatRoomClient()
        client.run()
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
