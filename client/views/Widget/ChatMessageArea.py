#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QTextBrowser, QVBoxLayout
from PyQt5.QtGui import QTextCursor, QFont
from PyQt5.QtCore import Qt
# 移除对旧Message模型的依赖，只使用VO
from client.models.vo import MessageVO  # 使用新的VO


class ChatMessageArea(QWidget):
    def __init__(self, current_user: str = None):
        super().__init__()
        self._current_user = current_user  # 设置当前用户信息
        self.init_ui()

    def init_ui(self):
        # 1. 主消息显示区域（QTextBrowser）
        self.msg_browser = QTextBrowser()
        self.msg_browser.setReadOnly(True)  # 只读，防止编辑
        self.msg_browser.setFont(QFont("Microsoft YaHei", 12))
        # 设置默认样式（解决中文显示+基础排版）
        self.msg_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #fafafa;
                background-image: linear-gradient(to bottom, #fafafa 0%, #f5f5f5 100%);
                border: none;
                border-radius: 12px;
                padding: 20px;
                font-family: 'Microsoft YaHei', sans-serif;
                line-height: 1.5;
            }
        """)

        # 布局
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(self.msg_browser, stretch=1)  # 占满大部分空间
        self.setLayout(layout)
        # 设置组件本身的样式
        self.setStyleSheet("""
            ChatMessageArea {
                background-color: #f0f0f0;
                border-radius: 16px;
                box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.08);
            }
        """)

    def add_system_message(self, content):
        """添加系统消息"""
        # 确保每个系统消息都独立显示，添加换行符确保分离
        style = '''
            <div style="text-align: center; margin: 16px 0; clear: both; display: block; overflow: hidden;">
                <span style="background-color: #e3f2fd; color: #1976d2; 
                            padding: 10px 18px; border-radius: 16px;
                            font-size: 12px; display: inline-block;
                            font-style: italic;
                            border: 1px solid #bbdefb; font-weight: 500;">
                    %s
                </span>
            </div>
            <br>
        ''' % content
        self.msg_browser.insertHtml(style)
        self.msg_browser.moveCursor(QTextCursor.End)

    def add_message(self, message):
        """添加普通消息 - 只支持新的MessageVO"""
        from common.log import log
        log.debug(f"消息区域添加消息: {message}")
        # 直接处理MessageVO对象
        self._add_vo_message(message)

    def _add_vo_message(self, message_vo):
        """添加新的MessageVO对象"""
        from common.log import log
        try:
            log.debug(f"_add_vo_message 接收到消息VO: {message_vo}")
            # 从VO中提取信息
            sender = getattr(message_vo, 'username', '未知用户')
            content = getattr(message_vo, 'content', '[无内容]')
            current_user = self._current_user  # 获取当前用户信息
            is_self = (current_user is not None and sender == current_user)  # 判断是否是自己发送的消息
            
            # 获取格式化时间
            time_str = message_vo.get_formatted_time()
            
            # 气泡样式CSS - 改进布局和美观度（移除box-shadow）
            if is_self:
                style = '''
                    <div style="margin: 16px 0; text-align: right;">
                        <div style="display: inline-block; text-align: left; max-width: 70%%;">
                            <div style="margin-bottom: 8px; font-size: 12px; color: #424242;">
                                <span style="font-weight: 600; color: #1976d2;">%s (我)</span>
                                <span style="margin-left: 8px; color: #9e9e9e; font-size: 11px;">%s</span>
                            </div>
                            <div style="background: linear-gradient(135deg, #2196f3 0%%, #21cbf3 100%%); color: white; 
                                       padding: 14px 18px; border-radius: 22px 8px 22px 22px; 
                                       display: inline-block;
                                       line-height: 1.6; word-break: break-word; font-size: 14px;">
                                %s
                            </div>
                        </div>
                    </div>
                ''' % (sender, time_str, content)
            else:
                style = '''
                    <div style="margin: 16px 0; text-align: left;">
                        <div style="display: inline-block; text-align: left; max-width: 70%%;">
                            <div style="margin-bottom: 8px; font-size: 12px; color: #424242;">
                                <span style="font-weight: 600; color: #424242;">%s</span>
                                <span style="margin-left: 8px; color: #9e9e9e; font-size: 11px;">%s</span>
                            </div>
                            <div style="background: linear-gradient(135deg, #ffffff 0%%, #f5f5f5 100%%); color: #212121; 
                                       padding: 14px 18px; border-radius: 8px 22px 22px 22px; 
                                       display: inline-block; border: 1px solid #e0e0e0;
                                       line-height: 1.6; word-break: break-word; font-size: 14px;">
                                %s
                            </div>
                        </div>
                    </div>
                ''' % (sender, time_str, content)
            # 插入到消息区域
            self.msg_browser.insertHtml(style)
            # 滚动到最底部
            self.msg_browser.moveCursor(QTextCursor.End)
            log.debug(f"消息已添加到界面: {content}")
        except Exception as e:
            log.error(f"添加消息时发生错误: {e}")
            import traceback
            traceback.print_exc()
