#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
注册视图
负责注册界面的展示和用户交互
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, \
    QTextEdit, QApplication
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

# 使用新的注册控制器
from client.controllers.register_controller import RegisterController
from common.config.config import config


class RegisterView(QMainWindow):
    """注册视图类"""

    username_input = None
    password_input = None
    confirm_input = None
    email_input = None
    nickname_input = None

    register_btn = None
    cancel_btn = None

    # 信号定义
    register_success = pyqtSignal()  # 注册成功信号
    close_view = pyqtSignal()  # 关闭视图信号

    def __init__(self):
        super().__init__()
        # 使用RegisterController替代LoginController
        self.controller = RegisterController()
        self.setWindowTitle("用户注册")
        self.setFixedSize(600, 600)  # 增加窗口尺寸，提供更多空间
        self.center_window()
        self.setStyleSheet(f"background-color: {config.ui.windowBackgroundColor};")
        self.init_ui()
        self.connect_signals()

    def center_window(self):
        """居中窗口"""
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def init_ui(self):
        """初始化用户界面"""
        # 主窗口设置
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)  # 增加间距，避免拥挤
        main_layout.setContentsMargins(50, 50, 50, 50)  # 增加边距，改善视觉效果

        # 标题
        title_label = QLabel("用户注册")
        title_label.setFont(QFont(config.ui.font.family, config.ui.font.titleSize + 2, QFont.Bold))  # 增大标题字体
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #000000; margin-bottom: 20px; font-weight: bold;")  # 增加底部间距
        main_layout.addWidget(title_label)

        # 用户信息
        user_group_layout = QVBoxLayout()
        user_group_layout.setSpacing(10)  # 保持间距

        user_title = QLabel("用户信息")
        user_title.setFont(QFont(config.ui.font.family, config.ui.font.subtitleSize + 1, QFont.Bold))  # 增大标题字体
        user_title.setStyleSheet("color: #000000; margin: 8px 0; font-weight: bold;")  # 增加间距和字体粗细
        user_group_layout.addWidget(user_title)

        # 用户名
        username_layout = QHBoxLayout()
        username_label = QLabel("用户名:")
        username_label.setFixedWidth(120)  # 增加标签宽度
        username_label.setFont(QFont(config.ui.font.family, config.ui.font.normalSize))
        username_label.setStyleSheet("color: #000000;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setFont(QFont(config.ui.font.family, config.ui.font.normalSize))
        self.username_input.setMinimumHeight(36)  # 增加输入框高度
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;  /* 增加内边距 */
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #ffffff;
                color: #000000;
            }
        """)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        user_group_layout.addLayout(username_layout)

        # 密码
        password_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        password_label.setFixedWidth(120)  # 增加标签宽度
        password_label.setFont(QFont(config.ui.font.family, config.ui.font.normalSize))
        password_label.setStyleSheet("color: #000000;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码（至少6位）")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont(config.ui.font.family, config.ui.font.normalSize))
        self.password_input.setMinimumHeight(36)  # 增加输入框高度
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;  /* 增加内边距 */
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #ffffff;
                color: #000000;
            }
        """)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        user_group_layout.addLayout(password_layout)

        # 确认密码
        confirm_layout = QHBoxLayout()
        confirm_label = QLabel("确认密码:")
        confirm_label.setFixedWidth(120)  # 增加标签宽度
        confirm_label.setFont(QFont(config.ui.font.family, config.ui.font.normalSize))
        confirm_label.setStyleSheet("color: #000000;")
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("请再次输入密码")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setFont(QFont(config.ui.font.family, config.ui.font.normalSize))
        self.confirm_input.setMinimumHeight(36)  # 增加输入框高度
        self.confirm_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;  /* 增加内边距 */
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #ffffff;
                color: #000000;
            }
        """)
        confirm_layout.addWidget(confirm_label)
        confirm_layout.addWidget(self.confirm_input)
        user_group_layout.addLayout(confirm_layout)

        # 邮箱
        email_layout = QHBoxLayout()
        email_label = QLabel("邮箱:")
        email_label.setFixedWidth(120)  # 增加标签宽度
        email_label.setFont(QFont(config.ui.font.family, config.ui.font.normalSize))
        email_label.setStyleSheet("color: #000000;")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("请输入邮箱（可选）")
        self.email_input.setFont(QFont(config.ui.font.family, config.ui.font.normalSize))
        self.email_input.setMinimumHeight(36)  # 增加输入框高度
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;  /* 增加内边距 */
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #ffffff;
                color: #000000;
            }
        """)
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        user_group_layout.addLayout(email_layout)

        # 昵称
        nickname_layout = QHBoxLayout()
        nickname_label = QLabel("昵称:")
        nickname_label.setFixedWidth(120)  # 增加标签宽度
        nickname_label.setFont(QFont(config.ui.font.family, config.ui.font.normalSize))
        nickname_label.setStyleSheet("color: #000000;")
        self.nickname_input = QLineEdit()
        self.nickname_input.setPlaceholderText("请输入昵称（可选）")
        self.nickname_input.setFont(QFont(config.ui.font.family, config.ui.font.normalSize))
        self.nickname_input.setMinimumHeight(36)  # 增加输入框高度
        self.nickname_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;  /* 增加内边距 */
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #ffffff;
                color: #000000;
            }
        """)
        nickname_layout.addWidget(nickname_label)
        nickname_layout.addWidget(self.nickname_input)
        user_group_layout.addLayout(nickname_layout)

        main_layout.addLayout(user_group_layout)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)  # 保持间距

        self.register_btn = QPushButton("注册")
        self.register_btn.setFixedHeight(40)  # 增加按钮高度
        self.register_btn.setMinimumWidth(120)  # 增加按钮宽度
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 16px;  /* 增大字体 */
                padding: 12px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedHeight(40)  # 增加按钮高度
        self.cancel_btn.setMinimumWidth(120)  # 增加按钮宽度
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 16px;  /* 增大字体 */
                padding: 12px 20px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)

        button_layout.addWidget(self.register_btn)
        button_layout.addWidget(self.cancel_btn)

        main_layout.addLayout(button_layout)

        # 底部提示
        tip_label = QLabel("提示：用户名和密码不能为空，密码长度不能少于6位")
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setFont(QFont(config.ui.font.family, config.ui.font.normalSize))
        tip_label.setStyleSheet("color: #000000; margin-top: 20px; font-style: italic;")  # 增加间距和斜体
        main_layout.addWidget(tip_label)

        central_widget.setLayout(main_layout)

    def connect_signals(self):
        """连接信号和槽"""
        self.register_btn.clicked.connect(self.on_register)
        self.cancel_btn.clicked.connect(self.on_cancel)

        # 连接控制器信号
        self.controller.register_success.connect(self.on_register_success)
        self.controller.register_failed.connect(self.on_register_failed)

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

    def on_register_success(self, message: str):
        """注册成功处理"""
        QMessageBox.information(self, "注册成功", message)
        self.register_success.emit()
        self.close()

    def on_register_failed(self, error_msg: str):
        """注册失败处理"""
        QMessageBox.warning(self, "注册失败", error_msg)

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.close_view.emit()
        event.accept()