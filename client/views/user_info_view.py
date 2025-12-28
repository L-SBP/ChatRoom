#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户信息视图
负责用户信息的展示和修改
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from common.config.client.config import get_client_config
from client.network.network_manager import NetworkManager
from common.log import client_log as log

# 获取客户端配置
client_config = get_client_config()

# 获取网络管理器单例
network_manager = NetworkManager()


class UserInfoView(QMainWindow):
    """用户信息视图类"""

    # 信号定义
    back_to_chat = pyqtSignal()  # 返回聊天界面信号
    update_success = pyqtSignal(str)  # 更新成功信号

    def __init__(self, username: str, user_info: dict):
        super().__init__()
        self.username = username
        self.user_info = user_info
        self.init_ui()
        # 连接到网络管理器的系统消息信号，用于接收更新用户信息的响应
        network_manager.system_message.connect(self.on_system_message)

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle(client_config.ui.windowTitle + " - 用户信息")
        self.setFixedSize(400, 500)
        self.center_window()
        self.setStyleSheet(f"background-color: {client_config.ui.windowBackgroundColor};")

        # 主窗口设置
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(50, 50, 50, 50)

        # 标题
        title_label = QLabel("用户信息")
        title_label.setFont(QFont(client_config.ui.font.family, client_config.ui.font.titleSize, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #000000; margin-bottom: 20px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # 用户名（不可修改）
        username_layout = QHBoxLayout()
        username_label = QLabel("用户名:")
        username_label.setFixedWidth(80)
        username_label.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        username_label.setStyleSheet("color: #000000;")
        self.username_display = QLineEdit()
        self.username_display.setText(self.user_info.get('username', ''))
        self.username_display.setReadOnly(True)
        self.username_display.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        self.username_display.setMinimumHeight(36)
        self.username_display.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #f5f5f5;
                color: #666;
            }
        """)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_display)
        main_layout.addLayout(username_layout)

        # 显示名称
        display_name_layout = QHBoxLayout()
        display_name_label = QLabel("显示名称:")
        display_name_label.setFixedWidth(80)
        display_name_label.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        display_name_label.setStyleSheet("color: #000000;")
        self.display_name_input = QLineEdit()
        self.display_name_input.setText(self.user_info.get('display_name', ''))
        self.display_name_input.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        self.display_name_input.setMinimumHeight(36)
        self.display_name_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #ffffff;
                color: #000000;
            }
        """)
        display_name_layout.addWidget(display_name_label)
        display_name_layout.addWidget(self.display_name_input)
        main_layout.addLayout(display_name_layout)

        # 邮箱
        email_layout = QHBoxLayout()
        email_label = QLabel("邮箱:")
        email_label.setFixedWidth(80)
        email_label.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        email_label.setStyleSheet("color: #000000;")
        self.email_input = QLineEdit()
        self.email_input.setText(self.user_info.get('email', ''))
        self.email_input.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        self.email_input.setMinimumHeight(36)
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #ffffff;
                color: #000000;
            }
        """)
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        main_layout.addLayout(email_layout)

        # 手机号
        phone_layout = QHBoxLayout()
        phone_label = QLabel("手机号:")
        phone_label.setFixedWidth(80)
        phone_label.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        phone_label.setStyleSheet("color: #000000;")
        self.phone_input = QLineEdit()
        self.phone_input.setText(self.user_info.get('phone', ''))
        self.phone_input.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        self.phone_input.setMinimumHeight(36)
        self.phone_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #ffffff;
                color: #000000;
            }
        """)
        phone_layout.addWidget(phone_label)
        phone_layout.addWidget(self.phone_input)
        main_layout.addLayout(phone_layout)



        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # 更新按钮
        self.update_btn = QPushButton("更新")
        self.update_btn.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        self.update_btn.setMinimumHeight(36)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.update_btn.clicked.connect(self.on_update_clicked)
        button_layout.addWidget(self.update_btn)

        # 返回按钮
        self.back_btn = QPushButton("返回")
        self.back_btn.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        self.back_btn.setMinimumHeight(36)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border: none;
                padding: 6px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #757575;
            }
            QPushButton:pressed {
                background-color: #616161;
            }
        """)
        self.back_btn.clicked.connect(self.on_back_clicked)
        button_layout.addWidget(self.back_btn)

        main_layout.addLayout(button_layout)

        central_widget.setLayout(main_layout)

    def center_window(self):
        """窗口居中"""
        screen = self.screen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def get_user_info(self):
        """获取用户输入的信息"""
        return {
            'display_name': self.display_name_input.text(),
            'email': self.email_input.text(),
            'phone': self.phone_input.text()
        }

    def show_message(self, message: str, is_error: bool = False):
        """显示消息"""
        if is_error:
            QMessageBox.critical(self, "错误", message)
        else:
            QMessageBox.information(self, "提示", message)



    def on_back_clicked(self):
        """返回聊天界面"""
        self.back_to_chat.emit()
        self.close()
    
    def on_update_clicked(self):
        """更新用户信息"""
        updated_info = self.get_user_info()
        
        # 基本验证
        if updated_info['email'] and '@' not in updated_info['email']:
            self.show_message("请输入有效的邮箱地址", is_error=True)
            return
        
        if updated_info['phone'] and not updated_info['phone'].isdigit():
            self.show_message("手机号只能包含数字", is_error=True)
            return
        
        # 这里可以添加更多验证逻辑
        
        if network_manager.is_connected():
            data = {
                'type': 'update_user_info',
                'username': self.user_info['username'],
                'display_name': updated_info['display_name'],
                'email': updated_info['email'],
                'phone': updated_info['phone']
            }
            network_manager.send_data(data)
            
            # 临时禁用更新按钮以防止重复点击
            self.update_btn.setEnabled(False)
            self.update_btn.setText("更新中...")
        else:
            self.show_message("未连接到服务器，请稍后重试", is_error=True)

    def on_system_message(self, message: str):
        """处理系统消息，包括更新用户信息的响应"""
        if "用户信息更新成功" in message:
            # 更新成功，更新本地用户信息
            updated_info = self.get_user_info()
            self.user_info.update(updated_info)
            
            # 显示成功消息并发出信号
            self.show_message(message)
            self.update_success.emit(message)
            
            # 重新启用更新按钮
            self.update_btn.setEnabled(True)
            self.update_btn.setText("更新")
            
            # 返回聊天界面
            self.on_back_clicked()
        elif "更新用户信息失败" in message:
            # 更新失败
            self.show_message(message, is_error=True)
            
            # 重新启用更新按钮
            self.update_btn.setEnabled(True)
            self.update_btn.setText("更新")
