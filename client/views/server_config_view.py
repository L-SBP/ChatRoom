#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器配置视图
负责服务器配置界面的展示和用户交互
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, \
    QProgressBar, QApplication
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIntValidator

from client.network.network_manager import NetworkManager
from common.config.config import config


class ServerConfigView(QMainWindow):
    """服务器配置视图类"""

    server_host_input = None
    server_port_input = None

    connect_btn = None
    exit_btn = None

    # 信号定义
    connection_success = pyqtSignal(str, int)  # 连接成功信号，参数为主机和端口
    exit_app = pyqtSignal()  # 退出应用信号

    def __init__(self):
        super().__init__()
        self.network_manager = NetworkManager()
        self.network_manager.connection_status.connect(self.on_connection_status)
        self.connecting = False
        
        self.setWindowTitle("服务器配置")
        self.setFixedSize(500, 300)
        self.center_window()
        self.setStyleSheet(f"background-color: #f0f2f5;")
        self.init_ui()

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
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(50, 50, 50, 50)

        # 标题
        title_label = QLabel("服务器配置")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #000000; margin-bottom: 20px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # 服务器地址
        host_layout = QHBoxLayout()
        host_label = QLabel("服务器地址:")
        host_label.setFixedWidth(100)
        host_label.setFont(QFont("Microsoft YaHei", 12))
        host_label.setStyleSheet("color: #000000;")
        self.server_host_input = QLineEdit()
        self.server_host_input.setText(config.client.default_server_host)
        self.server_host_input.setFont(QFont("Microsoft YaHei", 12))
        self.server_host_input.setMinimumHeight(36)
        self.server_host_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #ffffff;
                color: #000000;
            }
        """)
        host_layout.addWidget(host_label)
        host_layout.addWidget(self.server_host_input)
        main_layout.addLayout(host_layout)

        # 端口号
        port_layout = QHBoxLayout()
        port_label = QLabel("端口号:")
        port_label.setFixedWidth(100)
        port_label.setFont(QFont("Microsoft YaHei", 12))
        port_label.setStyleSheet("color: #000000;")
        self.server_port_input = QLineEdit()
        self.server_port_input.setText(str(config.client.default_server_port))
        self.server_port_input.setFont(QFont("Microsoft YaHei", 12))
        self.server_port_input.setMinimumHeight(36)
        self.server_port_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #ffffff;
                color: #000000;
            }
        """)
        # 只允许输入数字
        self.server_port_input.setValidator(QIntValidator(1, 65535, self))
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.server_port_input)
        main_layout.addLayout(port_layout)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        self.connect_btn = QPushButton("连接")
        self.connect_btn.setFixedHeight(40)
        self.connect_btn.setMinimumWidth(100)
        self.connect_btn.setStyleSheet("""
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
        self.connect_btn.clicked.connect(self.on_connect)

        self.exit_btn = QPushButton("退出")
        self.exit_btn.setFixedHeight(40)
        self.exit_btn.setMinimumWidth(100)
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
        self.exit_btn.clicked.connect(self.on_exit)

        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.exit_btn)
        main_layout.addLayout(button_layout)

        # 进度条（初始隐藏）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # 不确定模式
        main_layout.addWidget(self.progress_bar)

        central_widget.setLayout(main_layout)

    def on_connect(self):
        """处理连接按钮点击"""
        if self.connecting:
            return

        server_host = self.server_host_input.text().strip()
        server_port = self.server_port_input.text().strip()

        if not server_host or not server_port:
            QMessageBox.warning(self, "配置错误", "请输入服务器地址和端口号")
            return

        try:
            port_num = int(server_port)
            if port_num < 1 or port_num > 65535:
                QMessageBox.warning(self, "配置错误", "端口号必须是1-65535之间的数字")
                return
        except ValueError:
            QMessageBox.warning(self, "配置错误", "端口号必须是数字")
            return

        # 开始连接
        self.connecting = True
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("连接中...")
        self.progress_bar.setVisible(True)

        # 尝试连接到服务器
        self.network_manager.connect_to_server(server_host, port_num)

    def on_connection_status(self, success: bool, message: str):
        """处理连接状态变化"""
        self.connecting = False
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("连接")
        self.progress_bar.setVisible(False)

        if success:
            # 连接成功，发射信号
            server_host = self.server_host_input.text().strip()
            server_port = int(self.server_port_input.text().strip())
            self.connection_success.emit(server_host, server_port)
        else:
            # 连接失败，显示错误消息
            QMessageBox.critical(self, "连接失败", f"无法连接到服务器: {message}")

    def on_exit(self):
        """处理退出按钮点击"""
        self.exit_app.emit()

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.exit_app.emit()
        event.accept()