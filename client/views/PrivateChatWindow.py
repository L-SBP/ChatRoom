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
    window_closed = pyqtSignal(str)  # conversation_id
    # 加载历史消息信号
    load_history = pyqtSignal(str, int)  # conversation_id, limit
    
    def __init__(self, conversation: ConversationVO, current_user: str, controller=None):
        super().__init__()
        self.conversation = conversation
        self.current_user = current_user
        self.controller = controller
        self.is_open = False
        
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
    
    def on_send_message(self):
        """发送消息"""
        content = self.message_input.toPlainText().strip()
        if content:
            log.debug(f"发送私聊消息: {content} 给 {self.chat_target}")
            
            # 发送消息信号
            self.send_message.emit(
                self.conversation.conversation_id, 
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
        if isinstance(message, PrivateMessageVO):
            # 调用消息区域的添加消息方法
            self.message_area.add_message(message)
            # 滚动到底部
            self.message_area.scroll_to_bottom()
            log.debug(f"添加私聊消息: {message.content[:50]}...")
        else:
            log.error(f"不是PrivateMessageVO类型: {type(message)}")
    
    def load_history_messages(self, messages: list):
        """加载历史消息"""
        if messages:
            # 先清空现有消息
            self.message_area.clear_messages()
            # 添加历史消息
            for message in messages:
                self.add_private_message(message)
            log.debug(f"加载历史消息成功，共{len(messages)}条")
    
    def show(self):
        """显示窗口"""
        super().show()
        self.is_open = True
        # 加载历史消息
        self.load_history.emit(self.conversation.conversation_id, 50)
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        self.is_open = False
        self.window_closed.emit(self.conversation.conversation_id)
        log.debug(f"私聊窗口关闭: {self.conversation.conversation_id}")
        event.accept()
    
    def bring_to_front(self):
        """将窗口置顶显示"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def update_conversation(self, conversation: ConversationVO):
        """更新会话信息"""
        self.conversation = conversation
    
    def get_conversation_id(self):
        """获取会话ID"""
        return self.conversation.conversation_id
    
    def get_chat_target(self):
        """获取聊天对象"""
        return self.chat_target
    
    def set_controller(self, controller):
        """设置控制器"""
        self.controller = controller
