#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息模型类
定义消息数据结构和基本操作
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import time
import json


@dataclass
class Message:
    """消息数据模型"""
    sender: str
    content: str
    message_type: str = "text"  # text, file, system
    timestamp: Optional[float] = None
    receiver: Optional[str] = None  # 私聊时的目标用户
    file_info: Optional[Dict[str, Any]] = None  # 文件信息
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.sender or not self.content:
            raise ValueError("发送者和消息内容不能为空")
        
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'type': 'message',
            'sender': self.sender,
            'content': self.content,
            'message_type': self.message_type,
            'timestamp': self.timestamp,
            'receiver': self.receiver,
            'file_info': self.file_info
        }
    
    def to_json(self) -> str:
        """转换为JSON格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        """从字典创建消息对象"""
        return cls(
            sender=data.get('sender', ''),
            content=data.get('content', ''),
            message_type=data.get('message_type', 'text'),
            timestamp=data.get('timestamp'),
            receiver=data.get('receiver'),
            file_info=data.get('file_info')
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """从JSON字符串创建消息对象"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_formatted_time(self) -> str:
        """获取格式化的时间字符串"""
        return time.strftime('%H:%M:%S', time.localtime(self.timestamp))
    
    def is_private(self) -> bool:
        """是否为私聊消息"""
        return self.receiver is not None and self.receiver != self.sender


class SystemMessage(Message):
    """系统消息类"""
    
    def __init__(self, content: str, timestamp: Optional[float] = None):
        super().__init__(
            sender="System",
            content=content,
            message_type="system",
            timestamp=timestamp
        )


class FileMessage(Message):
    """文件消息类"""
    
    def __init__(self, sender: str, filename: str, file_data: bytes, 
                 file_size: int, receiver: Optional[str] = None, timestamp: Optional[float] = None):
        file_info = {
            'filename': filename,
            'size': file_size,
            'data': file_data.decode('latin-1')  # 转换为字符串传输
        }
        super().__init__(
            sender=sender,
            content=f"发送文件: {filename} ({file_size} bytes)",
            message_type="file",
            timestamp=timestamp,
            receiver=receiver,
            file_info=file_info
        )


class MessageManager:
    """消息管理器"""
    
    def __init__(self):
        self.messages: list[Message] = []
        self.max_messages = 1000  # 最大消息数量
    
    def add_message(self, message: Message) -> None:
        """添加消息"""
        self.messages.append(message)
        
        # 限制消息数量
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
    
    def get_messages(self) -> list[Message]:
        """获取所有消息"""
        return self.messages.copy()
    
    def get_messages_by_sender(self, sender: str) -> list[Message]:
        """获取指定发送者的消息"""
        return [msg for msg in self.messages if msg.sender == sender]
    
    def get_messages_by_receiver(self, receiver: str) -> list[Message]:
        """获取指定接收者的消息"""
        return [msg for msg in self.messages if msg.receiver == receiver]
    
    def get_private_messages(self) -> list[Message]:
        """获取所有私聊消息"""
        return [msg for msg in self.messages if msg.is_private()]
    
    def get_file_messages(self) -> list[FileMessage]:
        """获取所有文件消息"""
        return [msg for msg in self.messages if msg.message_type == "file"]
    
    def clear_messages(self) -> None:
        """清空消息列表"""
        self.messages.clear()
