#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录视图
负责登录界面的展示和用户交互
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIntValidator

from client.controllers.login_controller import LoginController
from client.network.network_manager import NetworkManager
from common.config.client.config import get_client_config

# 获取客户端配置
client_config = get_client_config()


class LoginView(QMainWindow):
    """登录视图类"""
    
    # 信号定义
    login_success = pyqtSignal(str)  # 登录成功信号，参数为用户名
    show_register = pyqtSignal()     # 显示注册界面信号
    exit_app = pyqtSignal()          # 退出应用信号
    
    def __init__(self):
        super().__init__()
        self.login_controller = LoginController()
        self.login_controller.login_success.connect(self.on_login_success)
        self.login_controller.login_failed.connect(self.on_login_failed)
        self.network_manager = NetworkManager()  # 获取网络管理器实例
        
        self.init_ui()
        self.setup_connections()
        self.start_connection_status_check()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle(client_config.ui.windowTitle + " - 登录")
        self.setFixedSize(500, 400)
        self.center_window()
        self.setStyleSheet(f"background-color: {client_config.ui.windowBackgroundColor};")
        
        # 主窗口设置
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(50, 50, 50, 50)
        
        # 标题
        title_label = QLabel("用户登录")
        title_label.setFont(QFont(client_config.ui.font.family, client_config.ui.font.titleSize, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #000000; margin-bottom: 20px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # 用户名
        username_layout = QHBoxLayout()
        username_label = QLabel("用户名:")
        username_label.setFixedWidth(80)
        username_label.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        username_label.setStyleSheet("color: #000000;")
        self.username_input = QLineEdit()
        self.username_input.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        self.username_input.setMinimumHeight(36)
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #ffffff;
                color: #000000;
            }
        """)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        main_layout.addLayout(username_layout)
        
        # 密码
        password_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        password_label.setFixedWidth(80)
        password_label.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        password_label.setStyleSheet("color: #000000;")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        self.password_input.setMinimumHeight(36)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #ffffff;
                color: #000000;
            }
        """)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        main_layout.addLayout(password_layout)
        
        # 连接状态标签
        self.connection_status_label = QLabel("连接状态: 未连接")
        self.connection_status_label.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        self.connection_status_label.setAlignment(Qt.AlignCenter)
        self.connection_status_label.setStyleSheet("""
            QLabel {
                color: #ff0000;
                padding: 5px;
                border-radius: 5px;
                background-color: #f0f0f0;
            }
        """)
        main_layout.addWidget(self.connection_status_label)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.login_btn = QPushButton("登录")
        self.login_btn.setFixedHeight(40)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        self.register_btn = QPushButton("注册")
        self.register_btn.setFixedHeight(40)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 16px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        
        self.exit_btn = QPushButton("退出")
        self.exit_btn.setFixedHeight(40)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 16px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        
        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.register_btn)
        button_layout.addWidget(self.exit_btn)
        main_layout.addLayout(button_layout)
        
        central_widget.setLayout(main_layout)
    
    def center_window(self):
        """居中窗口"""
        screen = self.screen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def setup_connections(self):
        """设置信号与槽连接"""
        self.login_btn.clicked.connect(self.on_login)
        self.register_btn.clicked.connect(self.on_register)
        self.exit_btn.clicked.connect(self.on_exit)
        self.username_input.returnPressed.connect(self.on_login)
        self.password_input.returnPressed.connect(self.on_login)
        self.network_manager.connection_status.connect(self.on_connection_status_changed)
    
    def start_connection_status_check(self):
        """开始连接状态检查"""
        # 初始化时尝试连接默认服务器
        host, port = self.login_controller.get_server_config()
        self.network_manager.connect_to_server(host, port)
    
    def on_connection_status_changed(self, connected: bool, message: str):
        """处理连接状态改变"""
        if connected:
            self.connection_status_label.setText(f"连接状态: 已连接 ({message})")
            self.connection_status_label.setStyleSheet("""
                QLabel {
                    color: #008000;
                    padding: 5px;
                    border-radius: 5px;
                    background-color: #f0f0f0;
                }
            """)
        else:
            self.connection_status_label.setText(f"连接状态: 未连接 ({message})")
            self.connection_status_label.setStyleSheet("""
                QLabel {
                    color: #ff0000;
                    padding: 5px;
                    border-radius: 5px;
                    background-color: #f0f0f0;
                }
            """)
    
    def on_login(self):
        """处理登录按钮点击"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("登录失败")
            msg_box.setText("请输入用户名和密码")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {client_config.ui.windowBackgroundColor};
                    font-family: {client_config.ui.font.family};
                    font-size: {client_config.ui.font.normalSize}px;
                }}
                QMessageBox QLabel {{
                    color: #000000;
                    font-family: {client_config.ui.font.family};
                    font-size: {client_config.ui.font.normalSize}px;
                    font-weight: bold;
                }}
                QMessageBox QPushButton {{
                    background-color: #f0f0f0;
                    color: #000000;
                    border: 2px solid #888888;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-family: {client_config.ui.font.family};
                    font-size: {client_config.ui.font.normalSize + 1}px;
                    font-weight: bold;
                    min-width: 100px;
                }}
                QMessageBox QPushButton:hover {{
                    background-color: #e0e0e0;
                    border: 2px solid #666666;
                }}
                QMessageBox QPushButton:pressed {{
                    background-color: #c0c0c0;
                    border: 2px solid #444444;
                }}
            """)
            msg_box.exec_()
            return
            
        # 获取服务器配置
        server_host, server_port = self.login_controller.get_server_config()
        
        # 调用控制器进行登录
        self.login_controller.login(username, password, server_host, server_port)
    
    def on_register(self):
        """处理注册按钮点击"""
        self.show_register.emit()
    
    def on_exit(self):
        """处理退出按钮点击"""
        self.exit_app.emit()
    
    def on_login_success(self, username: str):
        """处理登录成功"""
        self.login_success.emit(username)
    
    def on_login_failed(self, message: str):
        """处理登录失败"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("登录失败")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {client_config.ui.windowBackgroundColor};
                font-family: {client_config.ui.font.family};
                font-size: {client_config.ui.font.normalSize}px;
            }}
            QMessageBox QLabel {{
                color: #000000;
                font-family: {client_config.ui.font.family};
                font-size: {client_config.ui.font.normalSize}px;
                font-weight: bold;
            }}
            QMessageBox QPushButton {{
                background-color: #f0f0f0;
                color: #000000;
                border: 2px solid #888888;
                padding: 8px 16px;
                border-radius: 6px;
                font-family: {client_config.ui.font.family};
                font-size: {client_config.ui.font.normalSize + 1}px;
                font-weight: bold;
                min-width: 100px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: #e0e0e0;
                border: 2px solid #666666;
            }}
            QMessageBox QPushButton:pressed {{
                background-color: #c0c0c0;
                border: 2px solid #444444;
            }}
        """)
        msg_box.exec_()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.exit_app.emit()
        event.accept()