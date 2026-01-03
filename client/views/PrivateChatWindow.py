#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QSplitter
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from client.views.Widget.ChatMessageArea import ChatMessageArea
from client.models.vo import PrivateMessageVO, ConversationVO
from common.log import client_log as log


class PrivateChatWindow(QMainWindow):
    """私聊窗口类"""
    # 发送消息信号
    send_message = pyqtSignal(str, str, str)  # conversation_id, content, target_username
    # 关闭窗口信号
    window_closed = pyqtSignal(str)  # chat_target
    # 加载历史消息信号
    load_history = pyqtSignal(str, int)  # conversation_id, limit
    
    def __init__(self, conversation: ConversationVO, current_user: str, controller=None):
        super().__init__()
        self.conversation = conversation
        self.current_user = current_user
        self.controller = controller
        self.is_open = False
        self.pending_messages = []  # 存储待发送的消息，当会话ID获取后发送
        
        # 根据当前用户确定聊天对象
        if conversation.user1_name == current_user:
            self.chat_target = conversation.user2_name
            self.chat_target_id = conversation.user2_id
        else:
            self.chat_target = conversation.user1_name
            self.chat_target_id = conversation.user1_id
        
        self.init_ui()
        self.init_connections()
        
    def init_ui(self):
        """初始化UI"""
        # 设置窗口标题
        self.setWindowTitle(f"私聊 - {self.chat_target}")
        # 设置窗口大小
        self.resize(600, 500)
        # 设置窗口最小大小
        self.setMinimumSize(500, 400)
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # 消息显示区域
        self.message_area = ChatMessageArea(current_user=self.current_user)
        main_layout.addWidget(self.message_area, stretch=1)
        
        # 输入区域布局
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        # 消息输入框
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.setMinimumHeight(60)
        self.message_input.setMaximumHeight(120)
        self.message_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Microsoft YaHei';
                font-size: 13px;
            }
        """)
        input_layout.addWidget(self.message_input, stretch=1)
        
        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.setMinimumWidth(80)
        self.send_button.setMinimumHeight(60)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: 'Microsoft YaHei';
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        input_layout.addWidget(self.send_button)
        
        main_layout.addLayout(input_layout)
        
        # 设置整体样式
        self.setStyleSheet("""
            PrivateChatWindow {
                background-color: #f0f2f5;
            }
        """)
    
    def init_connections(self):
        """初始化信号连接"""
        self.send_button.clicked.connect(self.on_send_message)
        self.message_input.textChanged.connect(self.on_input_text_changed)
        # 回车键发送消息
        self.message_input.keyPressEvent = self.on_key_press
        # 连接加载历史消息按钮
        self.message_area.load_history_btn.clicked.connect(self._load_more_messages)
        # 设置消息区域的加载更多方法
        self.message_area._load_more_messages = self._load_more_messages
    
    def on_send_message(self):
        """发送消息"""
        content = self.message_input.toPlainText().strip()
        if content:
            log.debug(f"发送私聊消息: {content} 给 {self.chat_target}")
            
            # 如果还没有会话ID，先获取或创建会话
            conversation_id = self.conversation.conversation_id if self.conversation else ""
            if not conversation_id and self.controller:
                log.debug(f"没有会话ID，先获取或创建与{self.chat_target}的会话")
                self.controller.get_or_create_conversation(self.current_user, self.chat_target)
                # 暂时将消息存储到待发送列表
                self.pending_messages.append(content)
                self.message_input.clear()
                return
            
            # 发送消息信号
            self.send_message.emit(
                conversation_id, 
                content, 
                self.chat_target
            )
            
            # 清空输入框
            self.message_input.clear()
    
    def on_input_text_changed(self):
        """输入框内容变化时的处理"""
        content = self.message_input.toPlainText().strip()
        self.send_button.setEnabled(bool(content))
    
    def on_key_press(self, event):
        """键盘事件处理"""
        # 当按下回车键且没有按下Shift键时发送消息
        if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
            self.on_send_message()
        else:
            # 调用默认的keyPressEvent方法处理其他按键
            QTextEdit.keyPressEvent(self.message_input, event)
    
    def add_private_message(self, message: PrivateMessageVO):
        """添加私聊消息"""
        log.debug(f"PrivateChatWindow.add_private_message called with message: {message}")
        if isinstance(message, PrivateMessageVO):
            # 根据消息发送者判断显示样式
            if message.username == self.current_user:
                # 自己发送的消息
                log.debug(f"Adding own message to chat area: {message.content[:50]}...")
                self.message_area.add_message(message)
            else:
                # 接收的消息
                log.debug(f"Adding received message to chat area: {message.content[:50]}...")
                self.message_area.add_message(message)
            # 滚动到底部
            self.message_area.scroll_to_bottom()
            log.debug(f"Added private message: {message.content[:50]}...")
        else:
            log.error(f"add_private_message: Not a PrivateMessageVO type: {type(message)}")
    
    def load_history_messages(self, messages: list):
        """加载历史消息"""
        if messages:
            # 先清空现有消息
            self.message_area.clear_messages()
            # 添加历史消息
            for message in messages:
                self.add_private_message(message)
            log.debug(f"加载历史消息成功，共{len(messages)}条")
        # 重置加载状态
        self.message_area._is_loading = False
        self.message_area.load_history_btn.setEnabled(True)
    
    def _load_more_messages(self):
        """加载更多历史消息"""
        # 避免重复加载
        if self.message_area._is_loading:
            return
        
        # 加载消息时禁用按钮并设置加载状态
        self.message_area._is_loading = True
        self.message_area.load_history_btn.setDisabled(True)
        
        # 如果有会话ID，直接加载历史消息
        if self.conversation and self.conversation.conversation_id:
            self.load_history.emit(self.conversation.conversation_id, 50)
            log.debug(f"PrivateChatWindow: 发送加载历史消息信号，会话ID: {self.conversation.conversation_id}")
        else:
            # 没有会话ID，获取或创建会话
            log.debug(f"PrivateChatWindow: 没有会话ID，无法加载历史消息")
            self.message_area._is_loading = False
            self.message_area.load_history_btn.setEnabled(True)

    def show(self):
        """显示窗口"""
        super().show()
        self.is_open = True
        # 如果有会话ID，直接加载历史消息
        if self.conversation and self.conversation.conversation_id:
            self.load_history.emit(self.conversation.conversation_id, 50)
        # 否则等待会话ID更新后再加载历史消息

    def closeEvent(self, event):
        """关闭窗口事件"""
        self.is_open = False
        self.window_closed.emit(self.chat_target)
        log.debug(f"私聊窗口关闭: {self.chat_target}")
        event.accept()
    
    def bring_to_front(self):
        """将窗口置顶显示"""
        log.debug(f"PrivateChatWindow.bring_to_front called for {self.chat_target}")
        
        # 确保窗口是可见的
        if not self.isVisible():
            self.show()
            # 只有首次显示窗口时才居中
            self.move_to_center()
        
        # 将窗口置顶
        self.raise_()
        
        # 激活窗口
        self.activateWindow()
        
        # 确保窗口不被最小化
        if self.isMinimized():
            self.showNormal()
        
        log.debug(f"PrivateChatWindow.bring_to_front completed for {self.chat_target}")
        
    def move_to_center(self):
        """将窗口移到屏幕中央"""
        screen_geometry = self.screen().geometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())
    
    def update_conversation(self, conversation: ConversationVO):
        """更新会话信息"""
        old_conversation_id = self.conversation.conversation_id if self.conversation else ""
        self.conversation = conversation
        
        # 根据更新后的会话重新确定聊天对象
        if conversation.user1_name == self.current_user:
            self.chat_target = conversation.user2_name
            self.chat_target_id = conversation.user2_id
        else:
            self.chat_target = conversation.user1_name
            self.chat_target_id = conversation.user1_id
            
        # 更新窗口标题
        self.setWindowTitle(f"私聊 - {self.chat_target}")
        
        # 如果会话ID发生了变化，加载历史消息
        if conversation.conversation_id and conversation.conversation_id != old_conversation_id:
            self.load_history.emit(conversation.conversation_id, 50)
            
            # 发送待发送的消息
            if self.pending_messages:
                log.debug(f"发送待发送的消息，共 {len(self.pending_messages)} 条")
                for msg_content in self.pending_messages:
                    self.send_message.emit(
                        conversation.conversation_id,
                        msg_content,
                        self.chat_target
                    )
                # 清空待发送列表
                self.pending_messages.clear()
        
        self.activateWindow()
        # 确保窗口不被最小化
        if self.isMinimized():
            self.showNormal()
        
        # 检查是否有待发送消息，如果有则使用新的会话ID发送
        if conversation.conversation_id and self.pending_messages:
            log.debug(f"会话ID已获取，发送待发送消息列表，共{len(self.pending_messages)}条")
            for pending_content in self.pending_messages:
                # 发送消息信号
                self.send_message.emit(
                    conversation.conversation_id, 
                    pending_content, 
                    self.chat_target
                )
            # 清空待发送消息列表
            self.pending_messages.clear()
    
    def get_conversation_id(self):
        """获取会话ID"""
        return self.conversation.conversation_id
    
    def get_chat_target(self):
        """获取聊天对象"""
        return self.chat_target
    
    def set_controller(self, controller):
        """设置控制器"""
        self.controller = controller