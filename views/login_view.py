#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录视图
负责登录界面的展示和用户交互
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from controllers.login_controller import LoginController


class LoginView(QMainWindow):
    """登录视图类"""
    
    # 信号定义
    login_success = pyqtSignal(str)  # 登录成功信号，参数为用户名
    show_register = pyqtSignal()     # 显示注册界面信号
    exit_app = pyqtSignal()          # 退出应用信号
    
    def __init__(self):
        super().__init__()
        self.controller = LoginController()
        self.setWindowTitle("用户登录")
        self.setFixedSize(400, 350)
        self.init_ui()
        self.connect_signals()
        self.load_server_config()
    
    def init_ui(self):
        """初始化用户界面"""
        # 主窗口设置
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title_label = QLabel("聊天室登录")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 服务器配置
        server_group_layout = QVBoxLayout()
        server_group_layout.setSpacing(10)
        
        server_title = QLabel("服务器配置")
        server_title.setFont(QFont("Arial", 12, QFont.Bold))
        server_group_layout.addWidget(server_title)
        
        # 服务器地址
        server_layout = QHBoxLayout()
        server_label = QLabel("服务器地址:")
        server_label.setFixedWidth(100)
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("服务器IP地址，如：127.0.0.1")
        server_layout.addWidget(server_label)
        server_layout.addWidget(self.server_input)
        server_group_layout.addLayout(server_layout)
        
        # 端口号
        port_layout = QHBoxLayout()
        port_label = QLabel("端口号:")
        port_label.setFixedWidth(100)
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("服务器端口号，如：8888")
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        server_group_layout.addLayout(port_layout)
        
        main_layout.addLayout(server_group_layout)
        
        # 用户认证
        auth_group_layout = QVBoxLayout()
        auth_group_layout.setSpacing(10)
        
        auth_title = QLabel("用户认证")
        auth_title.setFont(QFont("Arial", 12, QFont.Bold))
        auth_group_layout.addWidget(auth_title)
        
        # 用户名
        username_layout = QHBoxLayout()
        username_label = QLabel("用户名:")
        username_label.setFixedWidth(100)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        auth_group_layout.addLayout(username_layout)
        
        # 密码
        password_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        password_label.setFixedWidth(100)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        auth_group_layout.addLayout(password_layout)
        
        # 记住密码
        self.remember_checkbox = QCheckBox("记住密码")
        auth_group_layout.addWidget(self.remember_checkbox)
        
        main_layout.addLayout(auth_group_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        self.login_btn = QPushButton("登录")
        self.login_btn.setFixedHeight(35)
        
        self.register_btn = QPushButton("注册")
        self.register_btn.setFixedHeight(35)
        
        self.cancel_btn = QPushButton("退出")
        self.cancel_btn.setFixedHeight(35)
        
        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.register_btn)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        # 底部提示
        tip_label = QLabel("提示：首次使用请先注册账户")
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setStyleSheet("color: gray;")
        main_layout.addWidget(tip_label)
        
        central_widget.setLayout(main_layout)
    
    def connect_signals(self):
        """连接信号和槽"""
        self.login_btn.clicked.connect(self.on_login)
        self.register_btn.clicked.connect(self.on_register)
        self.cancel_btn.clicked.connect(self.on_cancel)
        
        # 连接控制器信号
        self.controller.login_success.connect(self.on_login_success)
        self.controller.login_failed.connect(self.on_login_failed)
        self.controller.register_success.connect(self.on_register_success)
        self.controller.register_failed.connect(self.on_register_failed)
    
    def load_server_config(self):
        """加载服务器配置"""
        host, port = self.controller.get_server_config()
        self.server_input.setText(host)
        self.port_input.setText(str(port))
    
    def on_login(self):
        """处理登录按钮点击"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        server = self.server_input.text().strip()
        port = self.port_input.text().strip()
        
        # 保存服务器配置
        if server and port:
            try:
                port_num = int(port)
                self.controller.save_server_config(server, port_num)
            except ValueError:
                pass
        
        # 调用控制器处理登录
        self.controller.login(username, password, server, port)
    
    def on_register(self):
        """处理注册按钮点击"""
        self.show_register.emit()
    
    def on_cancel(self):
        """处理取消按钮点击"""
        self.exit_app.emit()
    
    def on_login_success(self, username: str):
        """登录成功处理"""
        self.login_success.emit(username)
        self.hide()
    
    def on_login_failed(self, error_msg: str):
        """登录失败处理"""
        QMessageBox.warning(self, "登录失败", error_msg)
    
    def on_register_success(self):
        """注册成功处理"""
        QMessageBox.information(self, "注册成功", "注册成功，请登录")
    
    def on_register_failed(self, error_msg: str):
        """注册失败处理"""
        QMessageBox.warning(self, "注册失败", error_msg)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.exit_app.emit()
        event.accept()
