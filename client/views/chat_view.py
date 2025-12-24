#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天视图
负责聊天界面的展示和用户交互
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, \
    QListWidget, QSplitter, QMenu, QAction, QMessageBox, QFileDialog, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCursor, QColor, QTextCharFormat
import time
import os

from client.controllers.chat_controller import ChatController
# 使用新的VO模型
from client.models.vo import MessageVO
from client.views.Widget.ChatMessageArea import ChatMessageArea
from common.config import get_client_config

client_config = get_client_config()


class ChatView(QMainWindow):
    """聊天视图类"""

    status_bar = None
    message_area = None
    message_input = None

    send_btn = None
    file_btn = None

    user_list = None

    # 信号定义
    close_view = pyqtSignal()  # 关闭视图信号

    def __init__(self, server_host: str, server_port: int, username: str):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.username = username
        self.setWindowTitle(f"聊天室 - {username}")
        self.setMinimumSize(client_config.ui.minWindowWidth, client_config.ui.minWindowHeight)
        self.resize(client_config.ui.windowWidth, client_config.ui.windowHeight)
        self.setStyleSheet(f"background-color: {client_config.ui.windowBackgroundColor};")

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
        self.status_bar.setStyleSheet(
            f"background-color: #e0e0e0; padding: 4px 8px; border-bottom: 1px solid #ccc; font-family: {client_config.ui.font.family}; color: #000000;")
        self.status_bar.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize - 1))
        self.status_bar.setFixedHeight(28)  # 减小状态栏高度
        main_layout.addWidget(self.status_bar)

        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(12)  # 增加分割线宽度，便于拖拽
        splitter.setChildrenCollapsible(False)  # 防止组件被完全折叠

        # 左侧聊天区域
        chat_widget = QWidget()
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(15, 15, 10, 15)  # 增加边距，改善视觉效果
        chat_layout.setSpacing(12)  # 增加间距，避免拥挤

        # 聊天标题
        chat_title = QLabel("聊天室")
        chat_title.setFont(QFont(client_config.ui.font.family, client_config.ui.font.titleSize, QFont.Bold))
        chat_title.setStyleSheet("color: #000000; padding: 5px 0;")
        chat_layout.addWidget(chat_title)

        # 消息显示区域
        self.message_area = ChatMessageArea(self.username)
        self.message_area.setMinimumHeight(400)
        self.message_area.setMaximumHeight(500)
        chat_layout.addWidget(self.message_area, 1)

        # 输入区域
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)  # 减小按钮间距

        # 消息输入框
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("请输入消息...")
        self.message_input.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        self.message_input.returnPressed.connect(self.send_message)
        self.message_input.setMinimumHeight(36)
        self.message_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px 12px;  /* 增加内边距，改善视觉效果 */
                border: 1px solid #aaa;
                border-radius: 6px;
                font-family: {client_config.ui.font.family};
                font-size: {client_config.ui.font.normalSize}px;
                background-color: #ffffff;
                color: #000000;
            }}
        """)
        input_layout.addWidget(self.message_input, 1)

        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.setMinimumWidth(100)
        self.send_btn.setMaximumWidth(140)
        self.send_btn.setMinimumHeight(36)  # 增加按钮高度
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 100px;
                max-width: 140px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        input_layout.addWidget(self.send_btn)

        # 文件发送按钮
        self.file_btn = QPushButton("文件")
        self.file_btn.setMinimumWidth(100)
        self.file_btn.setMaximumWidth(140)
        self.file_btn.setMinimumHeight(36)  # 增加按钮高度
        self.file_btn.clicked.connect(self.send_file)
        self.file_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 100px;
                max-width: 140px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        input_layout.addWidget(self.file_btn)

        chat_layout.addLayout(input_layout)

        chat_widget.setLayout(chat_layout)

        # 右侧用户列表
        user_widget = QWidget()
        user_layout = QVBoxLayout()
        user_layout.setContentsMargins(10, 15, 15, 15)  # 增加边距，改善视觉效果
        user_layout.setSpacing(12)  # 增加间距，避免拥挤

        # 用户列表标题
        user_title = QLabel("在线用户")
        user_title.setFont(QFont(client_config.ui.font.family, client_config.ui.font.subtitleSize, QFont.Bold))
        user_title.setStyleSheet("color: #000000; padding: 8px 0; font-weight: bold;")
        user_layout.addWidget(user_title)

        # 用户列表
        self.user_list = QListWidget()
        self.user_list.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        self.user_list.setMinimumHeight(300)  # 增加最小高度，显示更多用户
        self.user_list.setMaximumHeight(400)  # 设置最大高度，防止占用过多空间
        self.user_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #aaa;
                border-radius: 8px;
                padding: 8px;
                background-color: #ffffff;
                color: #000000;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-bottom: 1px solid #eee;
                color: #000000;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
                border-radius: 4px;
            }
            QListWidget::item:hover:!selected {
                background-color: #f0f0f0;
            }
            QListWidget::item:focus {
                outline: none;
            }
        """)
        user_layout.addWidget(self.user_list)

        # 私聊按钮
        private_chat_btn = QPushButton("私聊")
        private_chat_btn.setMinimumWidth(120)
        private_chat_btn.setMaximumWidth(160)
        private_chat_btn.setMinimumHeight(36)  # 增加按钮高度
        private_chat_btn.clicked.connect(self.start_private_chat)
        private_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
                max-width: 160px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #EF6C00;
            }
        """)
        user_layout.addWidget(private_chat_btn)

        # 刷新按钮
        refresh_btn = QPushButton("刷新用户")
        refresh_btn.setMinimumWidth(120)
        refresh_btn.setMaximumWidth(160)
        refresh_btn.setMinimumHeight(36)  # 增加按钮高度
        refresh_btn.clicked.connect(self.refresh_users)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
                max-width: 160px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
            QPushButton:pressed {
                background-color: #616161;
            }
        """)
        user_layout.addWidget(refresh_btn)

        user_widget.setLayout(user_layout)

        # 添加到分割器
        splitter.addWidget(chat_widget)
        splitter.addWidget(user_widget)
        splitter.setSizes([650, 250])  # 减小聊天区域宽度，节省水平空间
        splitter.setStretchFactor(0, 1)  # 让聊天区域可以拉伸
        splitter.setStretchFactor(1, 0)  # 用户列表区域不拉伸
        splitter.setMinimumWidth(750)  # 调整分割器最小宽度

        main_layout.addWidget(splitter)

        # 底部状态
        self.bottom_status = QLabel("就绪")
        self.bottom_status.setStyleSheet(
            "background-color: #e0e0e0; padding: 2px 5px; border-top: 1px solid #ccc; font-family: " + client_config.ui.font.family + "; color: #000000;")
        self.bottom_status.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize - 2))
        self.bottom_status.setFixedHeight(24)  # 减小底部状态栏高度
        main_layout.addWidget(self.bottom_status)

        central_widget.setLayout(main_layout)

    def connect_to_server(self):
        """使用现有的连接"""
        if self.controller.use_existing_connection(self.username):
            self.bottom_status.setText(f"已连接 - 用户: {self.username}")
            self.bottom_status.setStyleSheet(
                "background-color: #C8E6C9; padding: 5px; border-top: 1px solid #ccc; color: #2E7D32; font-family: " + client_config.ui.font.family + ";")
            # 添加连接成功的系统消息
            self.add_system_message(f"✓ 已连接到聊天室，欢迎 {self.username}！")
        else:
            self.bottom_status.setText("连接已断开")
            self.bottom_status.setStyleSheet(
                "background-color: #FFCDD2; padding: 5px; border-top: 1px solid #ccc; color: #C62828; font-family: " + client_config.ui.font.family + ";")
            self.add_system_message("✗ 连接失败，请检查网络连接")

    def on_message_received(self, message_obj):
        """处理接收到的消息"""
        from common.log import log
        log.debug(f"视图接收到消息对象: {message_obj}")
        
        try:
            # 检查消息对象类型
            if hasattr(message_obj, 'content_type'):
                # 如果是VO对象
                content_type = message_obj.content_type
                
                if content_type == "system":
                    # 处理系统消息
                    content = getattr(message_obj, 'content', '')
                    self.add_system_message(content)
                else:
                    # 普通消息
                    self.message_area.add_message(message_obj)
                    # 确保滚动到底部
                    QTimer.singleShot(100, self.message_area.scroll_to_bottom)
            elif isinstance(message_obj, dict):
                # 如果是字典格式
                if message_obj.get('content_type') == 'system':
                    self.add_system_message(message_obj.get('content', ''))
                else:
                    self.message_area.add_message(message_obj)
                    QTimer.singleShot(100, self.message_area.scroll_to_bottom)
            else:
                log.error(f"未知的消息格式: {type(message_obj)}")
                self.add_system_message(f"消息格式错误: {type(message_obj)}")
                
        except Exception as e:
            log.error(f"处理消息时出错: {e}")
            import traceback
            traceback.print_exc()
            self.add_system_message("消息处理错误")

    def on_user_list_updated(self, users: list):
        """处理用户列表更新"""
        self.user_list.clear()
        for user in users:
            self.user_list.addItem(user)

    def on_connection_established(self):
        """处理连接建立成功"""
        self.bottom_status.setText("已连接到服务器")
        self.bottom_status.setStyleSheet(
            "background-color: #C8E6C9; padding: 5px; border-top: 1px solid #ccc; color: #2E7D32; font-family: " + client_config.ui.font.family + ";")

    def on_connection_failed(self, message: str):
        """处理连接失败"""
        self.bottom_status.setText(f"连接失败: {message}")
        self.bottom_status.setStyleSheet(
            "background-color: #FFCDD2; padding: 5px; border-top: 1px solid #ccc; color: #C62828; font-family: " + client_config.ui.font.family + ";")

    def on_file_received(self, filename: str, file_path: str):
        """处理接收到的文件"""
        self.message_area.add_system_message(f"文件 '{filename}' 已接收并保存到: {file_path}")

    def on_system_message(self, message: str):
        """处理系统消息"""
        self.add_system_message(message)

    def send_message(self):
        """发送消息"""
        message = self.message_input.text().strip()
        if message:
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
        self.message_area.add_system_message(message)

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 创建自定义QMessageBox
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('退出')
        msg_box.setText('确定要退出聊天室吗？')
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowFlags(msg_box.windowFlags() & ~Qt.WindowContextHelpButtonHint)  # 去掉帮助按钮

        # 1. 手动创建按钮（指定文本）
        yes_btn = QPushButton("是")
        no_btn = QPushButton("否")
        msg_box.addButton(yes_btn, QMessageBox.YesRole)
        msg_box.addButton(no_btn, QMessageBox.NoRole)
        msg_box.setDefaultButton(no_btn)

        # 2. 调整“是”按钮样式（缩小尺寸+字体纯白加粗）
        yes_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32; /* 深绿色背景 */
                color: #FFFFFF !important; /* 强制纯白文字，避免变浅 */
                border: none;
                padding: 8px 16px; /* 缩小内边距，按钮变小 */
                border-radius: 6px; /* 圆角适中 */
                font-family: %s;
                font-size: %dpx; /* 字体大小适中 */
                font-weight: bold !important; /* 强制加粗，文字更醒目 */
                min-width: 80px; /* 缩小最小宽度 */
                min-height: 36px; /* 缩小最小高度 */
            }
            QPushButton:hover {
                background-color: #1B5E20; /* hover加深 */
            }
            QPushButton:pressed {
                background-color: #08330C; /* 按下更暗 */
            }
        """ % (client_config.ui.font.family, client_config.ui.font.normalSize + 1))

        # 3. 调整“否”按钮样式（和“是”按钮尺寸一致）
        no_btn.setStyleSheet("""
            QPushButton {
                background-color: #616161; /* 深灰色背景 */
                color: #FFFFFF !important; /* 强制纯白文字，避免变浅 */
                border: none;
                padding: 8px 16px; /* 缩小内边距 */
                border-radius: 6px; /* 圆角适中 */
                font-family: %s;
                font-size: %dpx; /* 字体大小适中 */
                font-weight: bold !important; /* 强制加粗 */
                min-width: 80px; /* 缩小最小宽度 */
                min-height: 36px; /* 缩小最小高度 */
            }
            QPushButton:hover {
                background-color: #424242; /* hover加深 */
            }
            QPushButton:pressed {
                background-color: #212121; /* 按下更暗 */
            }
        """ % (client_config.ui.font.family, client_config.ui.font.normalSize + 1))

        # 4. 调整弹窗布局（边距适中）
        msg_box.layout().setContentsMargins(15, 15, 15, 15)
        msg_box.layout().setSpacing(10)

        # 执行弹窗
        reply = msg_box.exec_()

        if msg_box.clickedButton() == yes_btn:
            # 直接退出应用
            QApplication.instance().quit()
            event.accept()
        else:
            event.ignore()
