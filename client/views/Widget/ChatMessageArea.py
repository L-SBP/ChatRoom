#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QTextBrowser, QVBoxLayout
from PyQt5.QtGui import QTextCursor, QFont
from PyQt5.QtCore import Qt
# 移除对旧Message模型的依赖，只使用VO
from client.models.vo import MessageVO  # 使用新的VO


class ChatMessageArea(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 1. 主消息显示区域（QTextBrowser）
        self.msg_browser = QTextBrowser()
        self.msg_browser.setReadOnly(True)  # 只读，防止编辑
        self.msg_browser.setFont(QFont("Microsoft YaHei", 12))
        # 设置默认样式（解决中文显示+基础排版）
        self.msg_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        # 布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.msg_browser, stretch=1)  # 占满大部分空间
        self.setLayout(layout)

    def add_system_message(self, content):
        """添加系统消息"""
        style = '''
            <p style="text-align: center; margin: 5px 0;">
                <span style="background-color: #e0e0e0; color: #666; 
                            padding: 4px 8px; border-radius: 4px;
                            font-size: 12px;">
                    %s
                </span>
            </p>
        ''' % content
        self.msg_browser.insertHtml(style)
        self.msg_browser.moveCursor(QTextCursor.End)

    def add_message(self, message):
        """添加普通消息 - 只支持新的MessageVO"""
        # 直接处理MessageVO对象
        self._add_vo_message(message)

    def _add_vo_message(self, message_vo):
        """添加新的MessageVO对象"""
        # 从VO中提取信息
        sender = getattr(message_vo, 'username', '未知用户')
        content = getattr(message_vo, 'content', '[无内容]')
        is_self = False  # 默认不是自己发送的消息
        
        # 气泡样式CSS
        if is_self:
            style = '''
                <div style="margin: 8px 0; text-align: right;">
                    <div style="display: inline-block; text-align: left; max-width: 70%%;">
                        <small style="color: #666;">%s (我)</small><br>
                        <div style="background-color: #4e89ff; color: white; 
                                   padding: 8px 12px; border-radius: 12px 0 12px 12px; 
                                   display: inline-block;">
                            %s
                        </div>
                    </div>
                </div>
            ''' % (sender, content)
        else:
            style = '''
                <div style="margin: 8px 0; text-align: left;">
                    <div style="display: inline-block; text-align: left; max-width: 70%%;">
                        <small style="color: #666;">%s</small><br>
                        <div style="background-color: #f0f0f0; color: #333; 
                                   padding: 8px 12px; border-radius: 0 12px 12px 12px; 
                                   display: inline-block;">
                            %s
                        </div>
                    </div>
                </div>
            ''' % (sender, content)
        # 插入到消息区域
        self.msg_browser.insertHtml(style)
        # 滚动到最底部
        self.msg_browser.moveCursor(QTextCursor.End)
