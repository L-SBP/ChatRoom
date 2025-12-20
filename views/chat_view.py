#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天视图
负责聊天界面的展示和用户交互
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, QListWidget, QSplitter, QMenu, QAction, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCursor, QColor, QTextCharFormat
import time

from controllers.chat_controller import ChatController
from models.message import Message


class ChatView(QMainWindow):
    """聊天视图类"""
    
    # 信号定义
    close_view = pyqtSignal()  # 关闭视图信号
    
    def __init__(self, server_host: str, server_port: int, username: str):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.username = username
        self.setWindowTitle(f"聊天室 - {username}")
        self.setGeometry(100, 100, 1200, 700)
        
        # 初始化控制器
        self.controller = ChatController()
        self.controller.message_received.connect(self.on_message_received)
        self.controller.user_list_updated.connect(self.on_user_list_updated)
        self.controller.connection_established.connect(self.on_connection_established)
        self.controller.connection_failed.connect(self.on_connection_failed)
        self.controller.file_received.connect(self.on_file_received)
        self.controller.system_message.connect(self.on_system_message)
        
        # 初始化UI
        self.init_ui()
        
        # 连接到服务器
        self.connect_to_server()
    
    def init_ui(self):
        """初始化用户界面"""
        # 主窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部状态栏
        self.status_bar = QLabel(f"已连接到 {self.server_host}:{self.server_port} | 用户: {self.username}")
        self.status_bar.setStyleSheet("background-color: #f0f0f0; padding: 8px; border-bottom: 1px solid #ddd;")
        self.status_bar.setFont(QFont("Arial", 10))
        main_layout.addWidget(self.status_bar)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧聊天区域
        chat_widget = QWidget()
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(10, 10, 10, 10)
        chat_layout.setSpacing(10)
        
        # 聊天标题
        chat_title = QLabel("聊天室")
        chat_title.setFont(QFont("Arial", 14, QFont.Bold))
        chat_layout.addWidget(chat_title)
        
        # 消息显示区域
        self.message_area = QTextEdit()
        self.message_area.setReadOnly(True)
        self.message_area.setFont(QFont("Arial", 11))
        self.message_area.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                background-color: white;
            }
        """)
        chat_layout.addWidget(self.message_area, 1)
        
        # 输入区域
        input_layout = QHBoxLayout()
        
        # 消息输入框
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("请输入消息...")
        self.message_input.setFont(QFont("Arial", 11))
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input, 1)
        
        # 发送按钮
        self.send_btn = QPushButton("发送 (Enter)")
        self.send_btn.setFixedWidth(120)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        # 文件发送按钮
        self.file_btn = QPushButton("发送文件")
        self.file_btn.setFixedWidth(120)
        self.file_btn.clicked.connect(self.send_file)
        input_layout.addWidget(self.file_btn)
        
        chat_layout.addLayout(input_layout)
        
        chat_widget.setLayout(chat_layout)
        
        # 右侧用户列表
        user_widget = QWidget()
        user_layout = QVBoxLayout()
        user_layout.setContentsMargins(10, 10, 10, 10)
        user_layout.setSpacing(10)
        
        # 用户列表标题
        user_title = QLabel("在线用户")
        user_title.setFont(QFont("Arial", 14, QFont.Bold))
        user_layout.addWidget(user_title)
        
        # 用户列表
        self.user_list = QListWidget()
        self.user_list.setFont(QFont("Arial", 11))
        self.user_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e6f3ff;
                color: black;
            }
        """)
        user_layout.addWidget(self.user_list)
        
        # 私聊按钮
        private_chat_btn = QPushButton("私聊")
        private_chat_btn.clicked.connect(self.start_private_chat)
        user_layout.addWidget(private_chat_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新用户列表")
        refresh_btn.clicked.connect(self.refresh_users)
        user_layout.addWidget(refresh_btn)
        
        user_widget.setLayout(user_layout)
        
        # 添加到分割器
        splitter.addWidget(chat_widget)
        splitter.addWidget(user_widget)
        splitter.setSizes([700, 300])  # 默认比例
        
        main_layout.addWidget(splitter)
        
        # 底部状态
        self.bottom_status = QLabel("就绪")
        self.bottom_status.setStyleSheet("background-color: #f0f0f0; padding: 5px; border-top: 1px solid #ddd;")
        self.bottom_status.setFont(QFont("Arial", 9))
        main_layout.addWidget(self.bottom_status)
        
        central_widget.setLayout(main_layout)
    
    def connect_to_server(self):
        """连接到服务器"""
        # 这里需要密码，但视图层不应该知道密码
        # 可以通过配置文件或其他方式获取
        password = "default_password"  # 临时密码
        self.controller.connect_to_server(self.server_host, self.server_port, self.username, password)
    
    def on_message_received(self, message: Message):
        """处理接收到的消息"""
        # 设置文本格式
        cursor = self.message_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # 添加用户名和时间
        format_user = QTextCharFormat()
        format_user.setForeground(QColor("#007bff"))
        format_user.setFontWeight(QFont.Bold)
        
        format_time = QTextCharFormat()
        format_time.setForeground(QColor("#666"))
        format_time.setFontItalic(True)
        
        format_msg = QTextCharFormat()
        format_msg.setForeground(QColor("#333"))
        
        cursor.insertText(f"[{message.get_formatted_time()}] ", format_time)
        cursor.insertText(f"{message.sender}: ", format_user)
        cursor.insertText(f"{message.content}\n", format_msg)
        
        # 滚动到底部
        self.message_area.setTextCursor(cursor)
        self.message_area.ensureCursorVisible()
    
    def on_user_list_updated(self, users: list):
        """处理用户列表更新"""
        self.user_list.clear()
        for user in users:
            self.user_list.addItem(user)
    
    def on_connection_established(self):
        """处理连接建立成功"""
        self.bottom_status.setText("已连接到服务器")
        self.bottom_status.setStyleSheet("background-color: #d4edda; padding: 5px; border-top: 1px solid #ddd; color: #155724;")
    
    def on_connection_failed(self, message: str):
        """处理连接失败"""
        self.bottom_status.setText(f"连接失败: {message}")
        self.bottom_status.setStyleSheet("background-color: #f8d7da; padding: 5px; border-top: 1px solid #ddd; color: #721c24;")
    
    def on_file_received(self, filename: str, file_path: str):
        """处理接收到的文件"""
        self.add_system_message(f"文件 '{filename}' 已接收并保存到: {file_path}")
    
    def on_system_message(self, message: str):
        """处理系统消息"""
        self.add_system_message(message)
    
    def send_message(self):
        """发送消息"""
        message = self.message_input.text().strip()
        if message:
            # 显示自己的消息
            timestamp = time.strftime('%H:%M:%S')
            self.on_message_received(Message(
                sender=self.username,
                content=message,
                timestamp=time.time()
            ))
            
            # 发送到服务器
            self.controller.send_message(message)
            
            # 清空输入框
            self.message_input.clear()
    
    def send_file(self):
        """发送文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要发送的文件", "", "所有文件 (*.*)"
        )
        if file_path:
            success = self.controller.send_file(file_path)
            if not success:
                QMessageBox.warning(self, "发送失败", "文件发送失败，请检查连接")
    
    def start_private_chat(self):
        """开始私聊"""
        selected_items = self.user_list.selectedItems()
        if selected_items:
            target_user = selected_items[0].text()
            if target_user != self.username:
                self.controller.start_private_chat(target_user)
            else:
                self.add_system_message("不能与自己私聊")
        else:
            self.add_system_message("请先选择一个用户")
    
    def refresh_users(self):
        """刷新用户列表"""
        self.controller.refresh_user_list()
    
    def add_system_message(self, message: str):
        """添加系统消息"""
        cursor = self.message_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        format_sys = QTextCharFormat()
        format_sys.setForeground(QColor("#888"))
        format_sys.setFontItalic(True)
        
        timestamp = time.strftime('%H:%M:%S')
        cursor.insertText(f"[{timestamp}] 系统消息: {message}\n", format_sys)
        
        self.message_area.setTextCursor(cursor)
        self.message_area.ensureCursorVisible()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(
            self, '退出', '确定要退出聊天室吗？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.controller.disconnect_from_server()
            self.close_view.emit()
            event.accept()
        else:
            event.ignore()
