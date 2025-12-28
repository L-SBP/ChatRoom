#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天视图
负责聊天界面的展示和用户交互
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, \
    QListWidget, QSplitter, QMenu, QAction, QMessageBox, QFileDialog, QApplication, QToolButton
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCursor, QColor, QTextCharFormat
import time
import os

from client.controllers.chat_controller import ChatController
# 使用新的VO模型
from client.models.vo import MessageVO
from client.views.Widget.ChatMessageArea import ChatMessageArea
from common.config import get_client_config
from common.log import client_log as log

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
        self.controller.message_sent.connect(self.on_message_sent)  # 处理自己发送的消息
        self.controller.user_list_updated.connect(self.on_user_list_updated)
        self.controller.connection_established.connect(self.on_connection_established)
        self.controller.connection_failed.connect(self.on_connection_failed)
        self.controller.file_received.connect(self.on_file_received)
        self.controller.system_message.connect(self.on_system_message)

        # 初始化UI
        self.init_ui()

        # 设置消息区域的加载更多方法
        self.message_area._load_more_messages = self._load_more_messages
        # 重新连接按钮的clicked信号到新的方法
        self.message_area.load_history_btn.clicked.disconnect()
        self.message_area.load_history_btn.clicked.connect(self._load_more_messages)

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
            f"background-color: #e0e0e0; padding: 1px 4px; border-bottom: 1px solid #ccc; font-family: {client_config.ui.font.family}; color: #000000;")
        self.status_bar.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize - 2))
        self.status_bar.setFixedHeight(20)  # 进一步减小状态栏高度
        main_layout.addWidget(self.status_bar)

        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(8)  # 减小分割线宽度
        splitter.setChildrenCollapsible(False)  # 防止组件被完全折叠

        # 聊天区域
        chat_widget = QWidget()
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(3, 3, 1, 3)  # 进一步减小边距
        chat_layout.setSpacing(6)  # 进一步减小间距

        # 消息显示区域
        self.message_area = ChatMessageArea(self.username)
        self.message_area.setMinimumHeight(240)  # 进一步减小最小高度
        # 移除最大高度限制，让消息区域可以根据窗口大小自适应
        self.message_area.setStyleSheet("""
            ChatMessageArea {
                background-color: #f0f2f5;
            }
        """)
        chat_layout.addWidget(self.message_area, 1)

        # 输入区域容器
        input_container = QWidget()
        input_container.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 2px;
        """)
        
        # 输入区域垂直布局
        input_layout = QVBoxLayout(input_container)
        input_layout.setSpacing(3)  # 减小元素间距
        input_layout.setContentsMargins(0, 0, 0, 0)

        # 主输入区域水平布局
        main_input_layout = QHBoxLayout()
        main_input_layout.setSpacing(3)  # 减小元素间距
        main_input_layout.setContentsMargins(0, 0, 0, 0)

        # 媒体工具栏按钮
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(2)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        # 语音发送按钮
        self.voice_btn = QToolButton()
        self.voice_btn.setText("🎤")  # 语音图标
        self.voice_btn.setToolTip("发送语音")
        self.voice_btn.setMinimumSize(24, 24)
        self.voice_btn.setMaximumSize(24, 24)
        self.voice_btn.clicked.connect(self.send_voice)
        self.voice_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
                border-radius: 2px;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
        """)
        toolbar_layout.addWidget(self.voice_btn)
        
        # 图片发送按钮
        self.image_btn = QToolButton()
        self.image_btn.setText("🖼")  # 图片图标
        self.image_btn.setToolTip("发送图片")
        self.image_btn.setMinimumSize(24, 24)
        self.image_btn.setMaximumSize(24, 24)
        self.image_btn.clicked.connect(self.send_image)
        self.image_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
                border-radius: 2px;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
        """)
        toolbar_layout.addWidget(self.image_btn)
        
        # 视频发送按钮
        self.video_btn = QToolButton()
        self.video_btn.setText("🎬")  # 视频图标
        self.video_btn.setToolTip("发送视频")
        self.video_btn.setMinimumSize(24, 24)
        self.video_btn.setMaximumSize(24, 24)
        self.video_btn.clicked.connect(self.send_video)
        self.video_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
                border-radius: 2px;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
        """)
        toolbar_layout.addWidget(self.video_btn)
        
        # 文件发送按钮
        self.file_btn = QToolButton()
        self.file_btn.setText("📁")  # 文件图标
        self.file_btn.setToolTip("发送文件")
        self.file_btn.setMinimumSize(24, 24)
        self.file_btn.setMaximumSize(24, 24)
        self.file_btn.clicked.connect(self.send_file)
        self.file_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
                border-radius: 2px;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
        """)
        toolbar_layout.addWidget(self.file_btn)

        # 将媒体按钮添加到主输入布局
        main_input_layout.addLayout(toolbar_layout)

        # 消息输入框
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("请输入消息...")
        self.message_input.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize))
        self.message_input.setLineWrapMode(QTextEdit.WidgetWidth)
        self.message_input.setTabChangesFocus(True)
        self.message_input.textChanged.connect(self.update_input_height)
        self.message_input.installEventFilter(self)
        self.message_input.setMinimumHeight(32)  # 减小高度
        self.message_input.setMaximumHeight(40)  # 减小最大高度
        # 设置样式表，避免使用f-string的花括号转义问题
        self.message_input.setStyleSheet("""
            QTextEdit {
                padding: 3px 6px;
                border: 1px solid #ddd;
                border-radius: 16px;
                background-color: #ffffff;
                color: #000000;
            }
        """)
        main_input_layout.addWidget(self.message_input, 1)  # 让输入框占据剩余空间

        # 发送按钮
        self.send_btn = QPushButton("发送(S)")
        self.send_btn.setMinimumWidth(70)
        self.send_btn.setMaximumWidth(80)
        self.send_btn.setMinimumHeight(22)  # 调整按钮高度
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 2px 6px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 11px;
                min-width: 70px;
                max-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        main_input_layout.addWidget(self.send_btn, alignment=Qt.AlignVCenter)  # 垂直居中

        # 设置按钮
        self.settings_btn = QToolButton()
        self.settings_btn.setText("⚙")  # 设置图标
        self.settings_btn.setToolTip("设置")
        self.settings_btn.setMinimumSize(24, 24)
        self.settings_btn.setMaximumSize(24, 24)
        self.settings_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
                border-radius: 2px;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
        """)
        main_input_layout.addWidget(self.settings_btn, alignment=Qt.AlignVCenter)  # 垂直居中

        # 将主输入布局添加到输入区域垂直布局
        input_layout.addLayout(main_input_layout)

        chat_layout.addWidget(input_container)

        chat_widget.setLayout(chat_layout)

        # 右侧用户列表
        user_widget = QWidget()
        user_widget.setStyleSheet("background-color: #f0f2f5;")  # 设置与聊天区域一致的背景色
        user_layout = QVBoxLayout()
        user_layout.setContentsMargins(3, 3, 1, 3)  # 调整边距与聊天区域一致
        user_layout.setSpacing(3)  # 进一步减小间距，使标题与用户列表更紧凑

        # 用户列表标题
        user_title = QLabel("在线用户")
        user_title.setFont(QFont(client_config.ui.font.family, client_config.ui.font.subtitleSize - 1, QFont.Bold))
        user_title.setStyleSheet("color: #000000; padding: 2px 6px; font-weight: bold;")
        user_title.setFixedHeight(24)  # 设置固定高度，确保与聊天区域对齐
        user_layout.addWidget(user_title)

        # 用户列表
        self.user_list = QListWidget()
        self.user_list.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize - 2))
        self.user_list.setMinimumHeight(200)  # 进一步减小最小高度
        self.user_list.setMaximumHeight(240)  # 进一步减小最大高度
        self.user_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 6px;
                background-color: #ffffff;
                color: #000000;
            }
            QListWidget::item {
                padding: 3px 5px;
                border-bottom: 1px solid #eee;
                color: #000000;
                border-radius: 2px;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
                border-radius: 2px;
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
        private_chat_btn.setMinimumWidth(70)
        private_chat_btn.setMaximumWidth(100)
        private_chat_btn.setMinimumHeight(24)  # 减小按钮高度
        private_chat_btn.clicked.connect(self.start_private_chat)
        private_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
                min-width: 70px;
                max-width: 100px;
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
        refresh_btn.setMinimumWidth(70)
        refresh_btn.setMaximumWidth(100)
        refresh_btn.setMinimumHeight(24)  # 减小按钮高度
        refresh_btn.clicked.connect(self.refresh_users)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
                min-width: 70px;
                max-width: 100px;
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
        splitter.setSizes([450, 110])  # 进一步减小用户列表宽度
        splitter.setStretchFactor(0, 1)  # 让聊天区域可以拉伸
        splitter.setStretchFactor(1, 0)  # 用户列表区域不拉伸
        splitter.setMinimumWidth(500)  # 调整分割器最小宽度，适应更小的用户列表

        main_layout.addWidget(splitter)

        # 底部状态
        self.bottom_status = QLabel("就绪")
        self.bottom_status.setStyleSheet(
            "background-color: #e0e0e0; padding: 1px 4px; border-top: 1px solid #ccc; font-family: " + client_config.ui.font.family + "; color: #000000;")
        self.bottom_status.setFont(QFont(client_config.ui.font.family, client_config.ui.font.normalSize - 3))
        self.bottom_status.setFixedHeight(20)  # 减小底部状态栏高度
        main_layout.addWidget(self.bottom_status)

        central_widget.setLayout(main_layout)

    def connect_to_server(self):
        """使用现有的连接"""
        if self.controller.use_existing_connection(self.username):
            self.bottom_status.setText(f"已连接 - 用户: {self.username}")
            self.bottom_status.setStyleSheet(
                "background-color: #C8E6C9; padding: 1px 4px; border-top: 1px solid #ccc; color: #2E7D32; font-family: " + client_config.ui.font.family + ";")
            # 添加连接成功的系统消息
            self.add_system_message(f"✓ 已连接到聊天室，欢迎 {self.username}！")
            
            # 不自动加载历史消息，改为由用户通过按钮触发
            # 确保加载按钮可见
            self.message_area.set_load_button_visible(True)
        else:
            self.bottom_status.setText("连接已断开")
            self.bottom_status.setStyleSheet(
                "background-color: #FFCDD2; padding: 1px 4px; border-top: 1px solid #ccc; color: #C62828; font-family: " + client_config.ui.font.family + ";")
            self.add_system_message("✗ 连接失败，请检查网络连接")

    def on_message_received(self, message_obj):
        """处理接收到的消息"""
        log.debug(f"视图接收到消息对象: {message_obj}")
        
        try:
            # 检查是否是消息列表（历史消息）
            if isinstance(message_obj, list):
                log.debug(f"视图接收到历史消息列表，共 {len(message_obj)} 条消息")
                
                # 如果列表为空，隐藏加载按钮并重置加载状态
                if not message_obj:
                    self.message_area.set_load_button_visible(False)
                    self.message_area._is_loading = False
                    # 重新启用加载按钮
                    self.message_area.load_history_btn.setEnabled(True)
                    return
                
                # 服务器返回的消息是按时间正序排列的（最旧的在前面）[oldest, older, ..., newest]
                # 为了在界面上按时间顺序显示（最旧的在最上面），我们需要反转列表，从最新的历史消息开始插入
                # 这样最终的显示顺序才是正确的 [oldest, older, ..., newest]
                reversed_messages = message_obj[::-1]  # 反转列表
                
                for msg in reversed_messages:  # 从最新的历史消息开始插入
                    if hasattr(msg, 'content_type'):
                        self.message_area.insert_message_at_top(msg)
                    elif isinstance(msg, dict):
                        self.message_area.insert_message_at_top(msg)
                    
                    # 更新最旧的消息ID - 记录最旧的消息ID（列表中的最后一个消息，即最旧的）
                    # 因为我们反转了列表，最旧的消息现在是最后一个被处理的
                    if hasattr(msg, 'message_id') and msg.message_id:
                        self.message_area._oldest_message_id = msg.message_id
                
                # 所有历史消息插入完成后，重置加载状态
                self.message_area._is_loading = False
                # 重新启用加载按钮
                self.message_area.load_history_btn.setEnabled(True)
                return
                
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
                    # 只有当用户已经在底部时才自动滚动到底部
                    if self.message_area.should_auto_scroll():
                        QTimer.singleShot(100, self.message_area.scroll_to_bottom)
            elif isinstance(message_obj, dict):
                # 如果是字典格式
                if message_obj.get('content_type') == 'system':
                    self.add_system_message(message_obj.get('content', ''))
                else:
                    self.message_area.add_message(message_obj)
                    # 只有当用户已经在底部时才自动滚动到底部
                    if self.message_area.should_auto_scroll():
                        QTimer.singleShot(100, self.message_area.scroll_to_bottom)
            else:
                log.error(f"未知的消息格式: {type(message_obj)}")
                self.add_system_message(f"消息格式错误: {type(message_obj)}")
                
        except Exception as e:
            log.error(f"处理消息时出错: {e}")
            import traceback
            traceback.print_exc()
            self.add_system_message("消息处理错误")
            # 发生异常时也要重置加载状态
            self.message_area._is_loading = False
            # 发生异常时也要重新启用加载按钮
            self.message_area.load_history_btn.setEnabled(True)

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
        
        # 不自动加载历史消息，改为由用户通过按钮触发
        # 确保加载按钮可见
        self.message_area.set_load_button_visible(True)

    def on_connection_failed(self, message: str):
        """处理连接失败"""
        self.bottom_status.setText(f"连接失败: {message}")
        self.bottom_status.setStyleSheet(
            "background-color: #FFCDD2; padding: 5px; border-top: 1px solid #ccc; color: #C62828; font-family: " + client_config.ui.font.family + ";")

    def on_message_sent(self, message_vo):
        """处理自己发送的消息"""
        # 在界面中立即显示自己发送的消息
        self.message_area.add_message(message_vo)
        # 确保滚动到底部
        QTimer.singleShot(100, self.message_area.scroll_to_bottom)

    def on_file_received(self, filename: str, file_path: str):
        """处理接收到的文件"""
        self.message_area.add_system_message(f"文件 '{filename}' 已接收并保存到: {file_path}")

    def on_system_message(self, message: str):
        """处理系统消息"""
        self.add_system_message(message)

    def send_message(self):
        """发送消息"""
        message = self.message_input.toPlainText().strip()
        if message:
            # 发送到服务器
            success = self.controller.send_message(message)
            
            if success:
                # 发送成功，清空输入框
                self.message_input.clear()
            else:
                # 发送失败，保留消息内容并提示用户
                self.add_system_message("消息发送失败，请检查网络连接")

    def update_input_height(self):
        """自动调整输入框高度"""
        document = self.message_input.document()
        document_height = document.size().height()
        current_height = self.message_input.height()
        
        # 如果内容高度超过当前高度且未达到最大高度，则增加高度
        if document_height > current_height and current_height < self.message_input.maximumHeight():
            self.message_input.setMinimumHeight(int(document_height) + 20)  # 20是内边距
        # 如果内容高度减小且大于最小高度，则减小高度
        elif document_height < current_height and current_height > self.message_input.minimumHeight():
            new_height = max(int(document_height) + 20, self.message_input.minimumHeight())
            self.message_input.setMinimumHeight(new_height)

    def eventFilter(self, obj, event):
        """事件过滤器，处理Enter键发送消息"""
        from PyQt5.QtCore import QEvent
        if obj == self.message_input:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    if event.modifiers() == Qt.ShiftModifier:
                        # 按下Shift+Enter，插入换行符
                        return False
                    else:
                        # 直接按Enter，发送消息
                        self.send_message()
                        return True
        return super().eventFilter(obj, event)

    def send_file(self):
        """发送文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要发送的文件", "", "所有文件 (*.*)"
        )
        if file_path:
            success = self.controller.send_file(file_path)
            if not success:
                QMessageBox.warning(self, "发送失败", "文件发送失败，请检查连接")

    def send_voice(self):
        """发送语音"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要发送的语音文件", "", "音频文件 (*.mp3 *.wav *.ogg *.aac)"
        )
        if file_path:
            success = self.controller.send_voice(file_path)
            if not success:
                QMessageBox.warning(self, "发送失败", "语音发送失败，请检查连接")

    def send_image(self):
        """发送图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要发送的图片文件", "", "图片文件 (*.jpg *.jpeg *.png *.gif *.bmp)"
        )
        if file_path:
            success = self.controller.send_image(file_path)
            if not success:
                QMessageBox.warning(self, "发送失败", "图片发送失败，请检查连接")

    def send_video(self):
        """发送视频"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要发送的视频文件", "", "视频文件 (*.mp4 *.avi *.mov *.wmv *.flv)"
        )
        if file_path:
            success = self.controller.send_video(file_path)
            if not success:
                QMessageBox.warning(self, "发送失败", "视频发送失败，请检查连接")

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

    def _load_more_messages(self):
        """加载更多消息，重写ChatMessageArea的方法"""
        from PyQt5.QtCore import QTimer
        log.debug("加载更多历史消息")
        
        # 避免重复加载
        if self.message_area._is_loading:
            return
        
        # 设置加载状态
        self.message_area._is_loading = True
        
        try:
            # 获取当前最旧的消息ID，如果是首次加载则为None
            oldest_message_id = self.message_area._oldest_message_id
            
            # 调用控制器获取历史消息
            success = self.controller.get_history_messages(
                message_id=oldest_message_id,
                limit=50
            )
            
            if not success:
                log.error("获取历史消息失败")
                self.message_area._is_loading = False
                self.message_area.load_history_btn.setEnabled(False)  # 请求失败，暂时禁用按钮
                return
            
            # 添加超时机制，确保加载状态能正确重置
            def reset_load_state():
                if hasattr(self.message_area, '_is_loading') and self.message_area._is_loading:
                    log.warning("历史消息加载超时，重置加载状态")
                    self.message_area._is_loading = False
                    self.message_area.load_history_btn.setEnabled(True)
            
            # 设置5秒超时
            self._load_timeout_timer = QTimer(self)
            self._load_timeout_timer.setSingleShot(True)
            self._load_timeout_timer.timeout.connect(reset_load_state)
            self._load_timeout_timer.start(5000)
            
        except Exception as e:
            log.error(f"加载更多消息时发生错误: {e}")
            import traceback
            traceback.print_exc()
            self.message_area._is_loading = False
            self.message_area.load_history_btn.setEnabled(True)

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 创建自定义QMessageBox
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('退出')
        msg_box.setText('确定要退出聊天室吗？')
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowFlags(msg_box.windowFlags() & ~Qt.WindowContextHelpButtonHint)  # 去掉帮助按钮

        # 设置弹窗整体样式
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
            }
            QMessageBox::title {
                color: #000000;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 0 0 0;
            }
            QMessageBox QLabel {
                color: #000000 !important;
                font-size: 14px;
                font-weight: 500;
            }
        """)

        # 1. 手动创建按钮（指定文本）
        yes_btn = QPushButton("是")
        no_btn = QPushButton("否")
        msg_box.addButton(yes_btn, QMessageBox.YesRole)
        msg_box.addButton(no_btn, QMessageBox.NoRole)
        msg_box.setDefaultButton(no_btn)

        # 2. 调整“是”按钮样式（紧凑设计）
        yes_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32; /* 深绿色背景 */
                color: #FFFFFF !important; /* 强制纯白文字 */
                border: none;
                padding: 6px 16px;
                border-radius: 6px;
                font-weight: bold !important;
                font-size: 14px;
                min-width: 70px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #1B5E20; /* hover加深 */
            }
            QPushButton:pressed {
                background-color: #08330C; /* 按下更暗 */
            }
        """)

        # 3. 调整“否”按钮样式（紧凑设计）
        no_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5; /* 浅灰色背景 */
                color: #000000 !important; /* 黑色文字 */
                border: 1px solid #E0E0E0;
                padding: 6px 16px;
                border-radius: 6px;
                font-weight: bold !important;
                font-size: 14px;
                min-width: 70px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #E0E0E0; /* hover加深 */
            }
            QPushButton:pressed {
                background-color: #BDBDBD; /* 按下更暗 */
            }
        """)

        # 4. 调整弹窗布局（优化边距和间距）
        msg_box.layout().setContentsMargins(20, 20, 20, 20)
        msg_box.layout().setSpacing(15)

        # 执行弹窗
        reply = msg_box.exec_()

        if msg_box.clickedButton() == yes_btn:
            # 直接退出应用
            QApplication.instance().quit()
            event.accept()
        else:
            event.ignore()
