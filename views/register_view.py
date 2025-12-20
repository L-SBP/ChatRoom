#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
注册视图
负责注册界面的展示和用户交互
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTextEdit
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from controllers.login_controller import LoginController


class RegisterView(QMainWindow):
    """注册视图类"""
    
    # 信号定义
    register_success = pyqtSignal()  # 注册成功信号
    close_view = pyqtSignal()        # 关闭视图信号
    
    def __init__(self):
        super().__init__()
        self.controller = LoginController()
        self.setWindowTitle("用户注册")
        self.setFixedSize(400, 400)
        self.init_ui()
        self.connect_signals()
    
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
        title_label = QLabel("用户注册")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 用户信息
        user_group_layout = QVBoxLayout()
        user_group_layout.setSpacing(10)
        
        user_title = QLabel("用户信息")
        user_title.setFont(QFont("Arial", 12, QFont.Bold))
        user_group_layout.addWidget(user_title)
        
        # 用户名
        username_layout = QHBoxLayout()
        username_label = QLabel("用户名:")
        username_label.setFixedWidth(100)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        user_group_layout.addLayout(username_layout)
        
        # 密码
        password_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        password_label.setFixedWidth(100)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码（至少6位）")
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        user_group_layout.addLayout(password_layout)
        
        # 确认密码
        confirm_layout = QHBoxLayout()
        confirm_label = QLabel("确认密码:")
        confirm_label.setFixedWidth(100)
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("请再次输入密码")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        confirm_layout.addWidget(confirm_label)
        confirm_layout.addWidget(self.confirm_input)
        user_group_layout.addLayout(confirm_layout)
        
        # 邮箱
        email_layout = QHBoxLayout()
        email_label = QLabel("邮箱:")
        email_label.setFixedWidth(100)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("请输入邮箱（可选）")
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        user_group_layout.addLayout(email_layout)
        
        # 昵称
        nickname_layout = QHBoxLayout()
        nickname_label = QLabel("昵称:")
        nickname_label.setFixedWidth(100)
        self.nickname_input = QLineEdit()
        self.nickname_input.setPlaceholderText("请输入昵称（可选）")
        nickname_layout.addWidget(nickname_label)
        nickname_layout.addWidget(self.nickname_input)
        user_group_layout.addLayout(nickname_layout)
        
        main_layout.addLayout(user_group_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        self.register_btn = QPushButton("注册")
        self.register_btn.setFixedHeight(35)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedHeight(35)
        
        button_layout.addWidget(self.register_btn)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        # 用户列表
        user_list_layout = QVBoxLayout()
        user_list_layout.setSpacing(10)
        
        user_list_title = QLabel("现有用户")
        user_list_title.setFont(QFont("Arial", 12, QFont.Bold))
        user_list_layout.addWidget(user_list_title)
        
        self.user_list = QTextEdit()
        self.user_list.setReadOnly(True)
        self.user_list.setFont(QFont("Arial", 10))
        self.user_list.setFixedHeight(80)
        user_list_layout.addWidget(self.user_list)
        
        main_layout.addLayout(user_list_layout)
        
        # 底部提示
        tip_label = QLabel("提示：用户名和密码不能为空，密码长度不能少于6位")
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setStyleSheet("color: gray;")
        main_layout.addWidget(tip_label)
        
        central_widget.setLayout(main_layout)
        
        # 加载用户列表
        self.load_user_list()
    
    def connect_signals(self):
        """连接信号和槽"""
        self.register_btn.clicked.connect(self.on_register)
        self.cancel_btn.clicked.connect(self.on_cancel)
        
        # 连接控制器信号
        self.controller.register_success.connect(self.on_register_success)
        self.controller.register_failed.connect(self.on_register_failed)
    
    def load_user_list(self):
        """加载用户列表"""
        users = self.controller.get_user_list()
        if users:
            user_text = "\n".join(users)
            self.user_list.setPlainText(user_text)
        else:
            self.user_list.setPlainText("暂无用户")
    
    def on_register(self):
        """处理注册按钮点击"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_input.text().strip()
        email = self.email_input.text().strip()
        nickname = self.nickname_input.text().strip()
        
        # 验证输入
        if not username or not password:
            QMessageBox.warning(self, "注册失败", "用户名和密码不能为空")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "注册失败", "密码长度不能少于6位")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "注册失败", "两次输入的密码不一致")
            return
        
        # 调用控制器处理注册
        self.controller.register(username, password, email, nickname)
    
    def on_cancel(self):
        """处理取消按钮点击"""
        self.close_view.emit()
        self.close()
    
    def on_register_success(self):
        """注册成功处理"""
        QMessageBox.information(self, "注册成功", "注册成功，请登录")
        self.register_success.emit()
        self.close()
    
    def on_register_failed(self, error_msg: str):
        """注册失败处理"""
        QMessageBox.warning(self, "注册失败", error_msg)
        self.load_user_list()  # 刷新用户列表
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.close_view.emit()
        event.accept()
