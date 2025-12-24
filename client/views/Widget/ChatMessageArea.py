#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import html
from PyQt5.QtWidgets import QWidget, QTextBrowser, QVBoxLayout
from PyQt5.QtGui import QTextCursor, QFont
from PyQt5.QtCore import Qt
from client.models.vo import MessageVO
from common.log import log


class ChatMessageArea(QWidget):
    def __init__(self, current_user: str = None):
        super().__init__()
        self._current_user = current_user
        self._message_count = 0  # 消息计数器
        self.init_ui()

    def init_ui(self):
        # 主消息显示区域
        self.msg_browser = QTextBrowser()
        self.msg_browser.setReadOnly(True)
        # 调整全局字体大小，从12px增大到14px
        self.msg_browser.setFont(QFont("Microsoft YaHei", 14))
        
        # 简洁的样式表
        self.msg_browser.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                border: none;
                padding: 15px;
                font-family: 'Microsoft YaHei';
                line-height: 1.5;
                color: #333;
            }
        """)

        # 布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.msg_browser, stretch=1)
        self.setLayout(layout)
        
        # 设置背景
        self.setStyleSheet("""
            ChatMessageArea {
                background-color: #f0f2f5;
            }
        """)

    def add_system_message(self, content: str):
        """添加系统消息 - 确保独立显示且无背景色"""
        # 使用HTML格式确保每条消息独立显示，p标签会自动创建新段落
        # 显式设置样式：灰色文字、小号字体、上下边距确保间距
        # 调整系统消息字体大小，从12px增大到13px
        message_html = f"<p style='color: #666; font-size: 13px; margin: 8px 0;'>[系统消息] {content}</p>"
        # 添加一个空行，保持与普通消息的间隔一致
        spacing_html = "<p style='height: 10px;'></p>"
        self.msg_browser.append(message_html)
        self.msg_browser.append(spacing_html)
        
        log.debug(f"添加系统消息: {content}")

    def add_message(self, message):
        """添加普通消息"""
        log.debug(f"消息区域添加消息: {message}")
        
        if isinstance(message, MessageVO):
            self._add_vo_message(message)
        elif isinstance(message, dict):
            # 处理字典格式的消息
            message_vo = MessageVO.from_dict(message)
            self._add_vo_message(message_vo)
        else:
            log.error(f"未知的消息类型: {type(message)}")
            self.add_system_message(f"消息格式错误: {type(message)}")

    def _add_vo_message(self, message_vo: MessageVO):
        """添加MessageVO对象"""
        try:
            # 提取消息信息
            sender = getattr(message_vo, 'username', '未知用户')
            content = getattr(message_vo, 'content', '[无内容]')
            
            # 获取时间
            time_str = message_vo.get_formatted_time() if hasattr(message_vo, 'get_formatted_time') else ""
            
            # 生成消息ID用于调试
            self._message_count += 1
            msg_id = f"msg_{self._message_count:04d}"
            
            # HTML转义防止XSS和解析错误
            safe_content = html.escape(content)
            safe_sender = html.escape(sender)
            
            # 终极解决方案：使用极简HTML结构，只使用p和span标签
            # QTextBrowser对HTML支持有限，必须使用最基础的标签
            if self._current_user is not None and sender == self._current_user:
                # 自己发送的消息 - 极简结构
                # 1. 头部信息（左对齐）
                header_html = f"<p style='text-align: left; color: #888; font-size: 14px; margin: 5px 0;'>我 {time_str} ✓ 已发送</p>"
                # 2. 消息气泡（左对齐，蓝色背景，圆角）
                bubble_html = f"<p style='text-align: left; margin: 5px 0;'><span style='background: #007AFF; color: white; padding: 10px 15px; border-radius: 18px;'>{safe_content}</span></p>"
                # 3. 消息间隔
                spacing_html = "<p style='height: 10px;'></p>"
                
                # 确保普通消息在新段落中显示
                # 先添加一个空段落作为分隔
                self.msg_browser.append("")
                # 然后插入HTML内容
                self.msg_browser.insertHtml(header_html + bubble_html + spacing_html)
            else:
                # 他人发送的消息 - 极简结构
                # 1. 头部信息（左对齐）
                header_html = f"<p style='text-align: left; color: #888; font-size: 14px; margin: 5px 0;'>{safe_sender} {time_str}</p>"
                # 2. 消息气泡（左对齐，灰色背景，圆角）
                bubble_html = f"<p style='text-align: left; margin: 5px 0;'><span style='background: #E9E9EB; color: #333; padding: 10px 15px; border-radius: 18px;'>{safe_content}</span></p>"
                # 3. 消息间隔
                spacing_html = "<p style='height: 10px;'></p>"
                
                # 确保普通消息在新段落中显示
                # 先添加一个空段落作为分隔
                self.msg_browser.append("")
                # 然后插入HTML内容
                self.msg_browser.insertHtml(header_html + bubble_html + spacing_html)
            
            log.debug(f"消息已添加到界面: {content[:50]}...")
            
        except Exception as e:
            log.error(f"添加消息时发生错误: {e}")
            import traceback
            traceback.print_exc()
            # 显示错误消息
            self.add_system_message(f"消息显示错误: {str(e)[:50]}")

    def _limit_message_count(self, max_messages: int = 500):
        """限制消息数量，防止内存泄漏"""
        try:
            # 获取当前文档
            document = self.msg_browser.document()
            
            # 获取所有块（消息）
            blocks = []
            block = document.firstBlock()
            while block.isValid():
                blocks.append(block)
                block = block.next()
            
            # 如果消息过多，删除最早的消息
            if len(blocks) > max_messages:
                # 删除前100条消息
                cursor = QTextCursor(document)
                cursor.setPosition(0)
                for _ in range(min(100, len(blocks) - max_messages)):
                    cursor.movePosition(QTextCursor.NextBlock)
                cursor.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()
                
                log.debug(f"已清理旧消息，当前消息数: {len(blocks)}")
                
        except Exception as e:
            log.error(f"清理消息时出错: {e}")

    def clear_messages(self):
        """清空所有消息"""
        self.msg_browser.clear()
        self._message_count = 0
        log.debug("已清空所有消息")

    def scroll_to_bottom(self):
        """滚动到底部"""
        self.msg_browser.verticalScrollBar().setValue(
            self.msg_browser.verticalScrollBar().maximum()
        )
