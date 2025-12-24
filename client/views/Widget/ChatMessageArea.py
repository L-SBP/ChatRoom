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
        self.msg_browser.setFont(QFont("Microsoft YaHei", 12))
        
        # 统一的样式表 - 解决显示问题
        self.msg_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #f5f5f7;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                line-height: 1.6;
                color: #333333;
            }
            QTextBrowser QAbstractScrollArea::corner {
                background-color: transparent;
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
                border-radius: 8px;
            }
        """)

    def add_system_message(self, content: str):
        """添加系统消息 - 确保独立显示"""
        # HTML转义防止XSS和解析错误
        safe_content = html.escape(content)
        
        # 系统消息样式 - 使用绝对居中的独立块
        style = f'''
        <div style="
            margin: 12px 0;
            clear: both;
            display: block;
            overflow: hidden;
            text-align: center;
        ">
            <span style="
                background-color: #e8f4fd;
                color: #2c5282;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 12px;
                display: inline-block;
                font-weight: 500;
                border: 1px solid #bee3f8;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            ">
                ⓘ {safe_content}
            </span>
        </div>
        '''
        
        self._append_html(style)
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
            
            # HTML转义内容，防止XSS和解析错误
            safe_content = html.escape(content) if content else ''
            current_user = self._current_user
            is_self = (current_user is not None and sender == current_user)
            
            # 获取时间
            time_str = message_vo.get_formatted_time() if hasattr(message_vo, 'get_formatted_time') else ""
            
            # 生成消息ID用于调试
            self._message_count += 1
            msg_id = f"msg_{self._message_count:04d}"
            
            # 消息容器样式 - 使用浮动布局确保内容正确显示
            if is_self:
                # 自己发送的消息 - 右侧优化
                style = f'''
                <div id="{msg_id}" style="
                    margin: 8px 0;
                    clear: both;
                    overflow: hidden;
                ">
                    <!-- 消息容器：强制右对齐 -->
                    <div style="
                        float: right;
                        max-width: 65%;
                        text-align: right;
                    ">
                        <!-- 头部：我 + 时间 + 已发送（紧凑排列） -->
                        <div style="
                            font-size: 11px;
                            margin-bottom: 4px;
                            color: #666;
                            text-align: right;
                        ">
                            <span style="
                                color: #2b6cb0;
                                font-weight: 600;
                                font-size: 12px;
                            ">我</span>
                            <span style="
                                color: #888;
                                margin-left: 8px;
                            ">{time_str}</span>
                            <span style="
                                color: #48bb78;
                                margin-left: 6px;
                                font-size: 10px;
                            ">✓ 已发送</span>
                        </div>
                        
                        <!-- 消息气泡：纯色背景+清晰文字 -->
                        <div style="
                            background-color: #4299e1 !important;
                            color: white !important;
                            padding: 10px 14px;
                            border-radius: 16px 4px 16px 16px;
                            display: inline-block;
                            text-align: left;
                            line-height: 1.5;
                            word-break: break-word;
                            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                            font-size: 13px;
                            max-width: 100%;
                        ">
                            {safe_content}
                        </div>
                    </div>
                </div>
                '''
            else:
                # 他人发送的消息 - 左侧优化
                style = f'''
                <div id="{msg_id}" style="
                    margin: 8px 0;
                    clear: both;
                    overflow: hidden;
                ">
                    <!-- 消息容器：强制左对齐 -->
                    <div style="
                        float: left;
                        max-width: 65%;
                        text-align: left;
                    ">
                        <!-- 头部：用户名 + 时间 -->
                        <div style="
                            font-size: 11px;
                            margin-bottom: 4px;
                            color: #888;
                            text-align: left;
                        ">
                            <span style="
                                color: #2d3748;
                                font-weight: 600;
                                font-size: 12px;
                            ">{sender}</span>
                            <span style="
                                color: #888;
                                margin-left: 8px;
                            ">{time_str}</span>
                        </div>
                        
                        <!-- 消息气泡：柔和背景+无冗余边框 -->
                        <div style="
                            background-color: #f0f8fb !important;
                            color: #2d3748 !important;
                            padding: 10px 14px;
                            border-radius: 4px 16px 16px 16px;
                            display: inline-block;
                            line-height: 1.5;
                            word-break: break-word;
                            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                            font-size: 13px;
                            max-width: 100%;
                        ">
                            {safe_content}
                        </div>
                    </div>
                </div>
                '''
            
            self._append_html(style)
            log.debug(f"消息已添加到界面: {content[:50]}...")
            
        except Exception as e:
            log.error(f"添加消息时发生错误: {e}")
            import traceback
            traceback.print_exc()
            # 显示错误消息
            self.add_system_message(f"消息显示错误: {str(e)[:50]}")

    def _append_html(self, html_content: str):
        """安全地添加HTML内容"""
        cursor = self.msg_browser.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # 只保留必要的换行（删除多余的<br>）
        if cursor.position() > 0:
            cursor.insertHtml("<br>")
        
        cursor.insertHtml(html_content)
        # 移除这里的多余<br>，避免消息间距过大
        
        self.msg_browser.setTextCursor(cursor)
        self.msg_browser.ensureCursorVisible()
        
        # 限制消息数量，防止内存占用过大
        self._limit_message_count()

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
