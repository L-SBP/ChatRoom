#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import html
from PyQt5.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QPushButton
from PyQt5.QtGui import QTextCursor, QFont
from PyQt5.QtCore import Qt
from client.models.vo import MessageVO
from common.log import client_log as log


class ChatMessageArea(QWidget):
    def __init__(self, current_user: str = None):
        super().__init__()
        self._current_user = current_user
        self._message_count = 0  # 消息计数器
        self._is_loading = False  # 防止重复加载
        self._oldest_message_id = None  # 用于分页加载
        self.init_ui()
        self.init_scroll_event()

    def init_ui(self):
        # 主消息显示区域
        self.msg_browser = QTextEdit()
        self.msg_browser.setReadOnly(True)
        # 调整全局字体大小，从12px增大到14px
        self.msg_browser.setFont(QFont("Microsoft YaHei", 14))
        # 设置文档HTML时不解析链接
        self.msg_browser.document().setMetaInformation(self.msg_browser.document().DocumentUrl, "")
        
        # 简洁的样式表
        self.msg_browser.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                padding: 15px;
                font-family: 'Microsoft YaHei';
                line-height: 1.5;
                color: #333;
            }
            QTextEdit a {
                color: inherit !important;
                text-decoration: none !important;
            }
            QTextEdit * {
                color: inherit;
            }
        """)

        # 创建加载历史消息的按钮
        self.load_history_btn = QPushButton("加载历史消息")
        self.load_history_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px 16px;
                margin: 5px auto;
                font-family: 'Microsoft YaHei';
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #888888;
            }
        """)
        self.load_history_btn.clicked.connect(self._load_more_messages)

        # 布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.load_history_btn)
        layout.addWidget(self.msg_browser, stretch=1)
        self.setLayout(layout)
        
        # 设置背景
        self.setStyleSheet("""
            ChatMessageArea {
                background-color: #f0f2f5;
            }
        """)

    def init_scroll_event(self):
        """初始化滚动事件监听"""
        # 监听滚动条的valueChanged信号
        self.msg_browser.verticalScrollBar().valueChanged.connect(self._on_scroll)
        
    def _on_scroll(self, value):
        """处理滚动事件，不再自动加载历史消息"""
        # 移除自动加载逻辑，改为按钮触发加载
        pass

    def _load_more_messages(self):
        """加载更多消息的方法，需要在子类或使用该组件的地方实现"""
        # 避免重复加载
        if self._is_loading:
            return
        # 加载消息时禁用按钮并设置加载状态
        self._is_loading = True
        self.load_history_btn.setDisabled(True)
        log.debug("_load_more_messages方法被调用，需要在子类中实现")
    
    def set_load_button_visible(self, visible: bool):
        """设置加载按钮的可见性"""
        self.load_history_btn.setVisible(visible)
        log.debug(f"加载按钮可见性设置为: {visible}")

    def add_system_message(self, content: str):
        """添加系统消息 - 确保独立显示且无背景色"""
        # 使用HTML格式确保每条消息独立显示，p标签会自动创建新段落
        # 显式设置样式：灰色文字、小号字体、上下边距确保间距
        # 调整系统消息字体大小，从12px增大到13px
        message_html = f"<p style='color: #666; font-size: 13px; margin: 8px 0; text-decoration: none;'>[系统消息] {content}</p>"
        # 添加一个空行，保持与普通消息的间隔一致
        spacing_html = "<p style='height: 10px;'></p>"
        
        # 将系统消息添加到文档末尾
        full_html = message_html + spacing_html
        cursor = QTextCursor(self.msg_browser.document())
        cursor.movePosition(QTextCursor.End)
        self.msg_browser.setTextCursor(cursor)
        self.msg_browser.insertHtml(full_html)
        
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
            content_type = getattr(message_vo, 'content_type', 'text')
            file_vo = getattr(message_vo, 'file_vo', None)
            
            # 获取时间
            time_str = message_vo.get_formatted_time() if hasattr(message_vo, 'get_formatted_time') else ""
            
            # 生成消息ID用于调试
            self._message_count += 1
            msg_id = f"msg_{self._message_count:04d}"
            
            # HTML转义防止XSS和解析错误
            safe_content = html.escape(content)
            safe_sender = html.escape(sender)
            
            # 根据消息类型生成不同的显示内容
            def get_message_content_html(content_type, content, file_vo):
                if content_type in ['image', 'video', 'audio', 'file']:
                    # 媒体类型消息
                    if file_vo:
                        file_name = getattr(file_vo, 'file_name', '未知文件')
                        file_url = getattr(file_vo, 'file_url', '#')
                        file_size = getattr(file_vo, 'file_size', 0)
                        
                        # 格式化文件大小
                        def format_file_size(size_bytes):
                            if size_bytes < 1024:
                                return f"{size_bytes} B"
                            elif size_bytes < 1024 * 1024:
                                return f"{size_bytes / 1024:.1f} KB"
                            elif size_bytes < 1024 * 1024 * 1024:
                                return f"{size_bytes / (1024 * 1024):.1f} MB"
                            else:
                                return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
                        
                        file_size_str = format_file_size(file_size)
                        
                        if content_type == 'image':
                            # 图片消息 - 使用本地文件路径
                            return f"<img src='{file_url}' alt='图片' style='max-width: 300px; max-height: 300px; border-radius: 8px; object-fit: cover;'><br><small style='color: #666;'>{file_name} ({file_size_str})</small>"
                        elif content_type == 'video':
                            # 视频消息
                            return f"[视频文件] {file_name} ({file_size_str})"
                        elif content_type == 'audio':
                            # 音频消息
                            return f"[音频文件] {file_name} ({file_size_str})"
                        elif content_type == 'file':
                            # 文件文件
                            return f"[文件] {file_name} ({file_size_str})"
                    return "[媒体内容]"
                else:
                    # 文本消息
                    return safe_content
            
            message_content = get_message_content_html(content_type, content, file_vo)
            
            # 使用正确的HTML结构确保消息显示正常
            if self._current_user is not None and sender == self._current_user:
                # 自己发送的消息
                # 1. 头部信息（左对齐）
                header_html = f"<p style='text-align: left; color: #888; font-size: 14px; margin: 5px 0;'>我 {time_str} ✓ 已发送</p>"
                # 2. 消息气泡（左对齐，蓝色背景，圆角）
                bubble_html = f"<p style='text-align: left; margin: 5px 0;'><span style='background: #007AFF; color: white; padding: 10px 15px; border-radius: 18px; text-decoration: none;'>{message_content}</span></p>"
                # 3. 消息间隔
                spacing_html = "<p style='height: 10px;'></p>"
            else:
                # 他人发送的消息
                # 1. 头部信息（左对齐）
                header_html = f"<p style='text-align: left; color: #888; font-size: 14px; margin: 5px 0;'>{safe_sender} {time_str}</p>"
                # 2. 消息气泡（左对齐，灰色背景，圆角）
                bubble_html = f"<p style='text-align: left; margin: 5px 0;'><span style='background: #E9E9EB; color: #333; padding: 10px 15px; border-radius: 18px; text-decoration: none;'>{message_content}</span></p>"
                # 3. 消息间隔
                spacing_html = "<p style='height: 10px;'></p>"
            
            # 直接将HTML内容添加到文档末尾
            full_html = header_html + bubble_html + spacing_html
            # 先将光标移动到文档末尾，然后插入HTML
            cursor = QTextCursor(self.msg_browser.document())
            cursor.movePosition(QTextCursor.End)
            self.msg_browser.setTextCursor(cursor)
            self.msg_browser.insertHtml(full_html)
            
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
    
    def insert_message_at_top(self, message):
        """在顶部插入消息"""
        log.debug(f"在顶部插入消息: {message}")
        
        # 保存当前滚动位置
        current_scroll_value = self.msg_browser.verticalScrollBar().value()
        current_scroll_max = self.msg_browser.verticalScrollBar().maximum()
        
        # 获取当前文档高度
        current_height = self.msg_browser.document().size().height()
        
        # 将光标移动到文档开头
        cursor = QTextCursor(self.msg_browser.document())
        cursor.movePosition(QTextCursor.Start)
        self.msg_browser.setTextCursor(cursor)
        
        # 添加消息
        if isinstance(message, MessageVO):
            self._insert_vo_message_at_top(message)
        elif isinstance(message, dict):
            # 处理字典格式的消息
            message_vo = MessageVO.from_dict(message)
            self._insert_vo_message_at_top(message_vo)
        else:
            log.error(f"未知的消息类型: {type(message)}")
            self.add_system_message(f"消息格式错误: {type(message)}")
        
        # 计算新的文档高度
        new_height = self.msg_browser.document().size().height()
        
        # 计算高度差
        height_diff = new_height - current_height
        
        # 调整滚动位置，保持用户看到的内容不变
        if current_scroll_value > 0:
            # 如果用户不是在顶部，调整滚动位置以保持看到的内容不变
            new_scroll_value = current_scroll_value + height_diff
            self.msg_browser.verticalScrollBar().setValue(new_scroll_value)
    
    def _insert_vo_message_at_top(self, message_vo: MessageVO):
        """在顶部插入MessageVO对象"""
        try:
            # 提取消息信息
            sender = getattr(message_vo, 'username', '未知用户')
            content = getattr(message_vo, 'content', '[无内容]')
            content_type = getattr(message_vo, 'content_type', 'text')
            file_vo = getattr(message_vo, 'file_vo', None)
            
            # 获取时间
            time_str = message_vo.get_formatted_time() if hasattr(message_vo, 'get_formatted_time') else ""
            
            # 生成消息ID用于调试
            self._message_count += 1
            msg_id = f"msg_{self._message_count:04d}"
            
            # HTML转义防止XSS和解析错误
            safe_content = html.escape(content)
            safe_sender = html.escape(sender)
            
            # 根据消息类型生成不同的显示内容
            def get_message_content_html(content_type, content, file_vo):
                if content_type in ['image', 'video', 'audio', 'file']:
                    # 媒体类型消息
                    if file_vo:
                        file_name = getattr(file_vo, 'file_name', '未知文件')
                        file_url = getattr(file_vo, 'file_url', '#')
                        file_size = getattr(file_vo, 'file_size', 0)
                        
                        # 格式化文件大小
                        def format_file_size(size_bytes):
                            if size_bytes < 1024:
                                return f"{size_bytes} B"
                            elif size_bytes < 1024 * 1024:
                                return f"{size_bytes / 1024:.1f} KB"
                            elif size_bytes < 1024 * 1024 * 1024:
                                return f"{size_bytes / (1024 * 1024):.1f} MB"
                            else:
                                return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
                        
                        file_size_str = format_file_size(file_size)
                        
                        if content_type == 'image':
                            # 图片消息
                            return f"<img src='{file_url}' alt='图片' style='max-width: 300px; max-height: 300px; border-radius: 8px;'><br><small style='color: #666;'>{file_name} ({file_size_str})</small>"
                        elif content_type == 'video':
                            # 视频消息
                            return f"[视频文件] {file_name} ({file_size_str})"
                        elif content_type == 'audio':
                            # 音频消息
                            return f"[音频文件] {file_name} ({file_size_str})"
                        elif content_type == 'file':
                            # 文件消息
                            return f"[文件] {file_name} ({file_size_str})"
                    return "[媒体内容]"
                else:
                    # 文本消息
                    return safe_content
            
            message_content = get_message_content_html(content_type, content, file_vo)
            
            # 使用与add_message相同的HTML结构
            if self._current_user is not None and sender == self._current_user:
                # 自己发送的消息
                header_html = f"<p style='text-align: left; color: #888; font-size: 14px; margin: 5px 0;'>我 {time_str} ✓ 已发送</p>"
                bubble_html = f"<p style='text-align: left; margin: 5px 0;'><span style='background: #007AFF; color: white; padding: 10px 15px; border-radius: 18px; text-decoration: none;'>{message_content}</span></p>"
                spacing_html = "<p style='height: 10px;'></p>"
            else:
                # 他人发送的消息
                header_html = f"<p style='text-align: left; color: #888; font-size: 14px; margin: 5px 0;'>{safe_sender} {time_str}</p>"
                bubble_html = f"<p style='text-align: left; margin: 5px 0;'><span style='background: #E9E9EB; color: #333; padding: 10px 15px; border-radius: 18px; text-decoration: none;'>{message_content}</span></p>"
                spacing_html = "<p style='height: 10px;'></p>"
            
            # 插入HTML内容
            self.msg_browser.insertHtml(header_html + bubble_html + spacing_html)
            
            log.debug(f"消息已插入到顶部: {content[:50]}...")
            
        except Exception as e:
            log.error(f"在顶部插入消息时发生错误: {e}")
            import traceback
            traceback.print_exc()
            # 显示错误消息
            self.add_system_message(f"消息显示错误: {str(e)[:50]}")
