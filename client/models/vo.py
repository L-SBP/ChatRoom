#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VO模型
客户端视图对象，用于展示层数据封装
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class UserVO:
    """用户视图对象"""
    user_id: str
    username: str
    password: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str = "offline"  # offline/online/busy/away
    last_seen: Optional[datetime] = None
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        return self.display_name if self.display_name else self.username
    
    def is_online(self) -> bool:
        """判断用户是否在线"""
        return self.status == "online"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'password': self.password,
            'email': self.email,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'status': self.status,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserVO':
        """从字典创建UserVO对象"""
        # 处理时间戳
        last_seen = None
        if data.get('last_seen'):
            try:
                last_seen = datetime.fromisoformat(data['last_seen'])
            except ValueError:
                pass
        
        return cls(
            user_id=data.get('user_id', ''),
            username=data.get('username', ''),
            display_name=data.get('display_name'),
            avatar_url=data.get('avatar_url'),
            status=data.get('status', 'offline'),
            last_seen=last_seen
        )


@dataclass
class FileVO:
    """文件视图对象"""
    file_id: str
    file_name: str
    file_url: str
    file_type: Optional[str] = None  # image/video/audio/file
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None  # 音视频时长（秒）
    thumbnail_url: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'file_id': self.file_id,
            'file_name': self.file_name,
            'file_url': self.file_url,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'duration': self.duration,
            'thumbnail_url': self.thumbnail_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileVO':
        """从字典创建FileVO对象"""
        # 处理时间戳
        created_at = None
        if data.get('created_at'):
            try:
                created_at = datetime.fromisoformat(data['created_at'])
            except ValueError:
                pass
        
        return cls(
            file_id=data.get('file_id', ''),
            file_name=data.get('file_name', ''),
            file_url=data.get('file_url', ''),
            file_type=data.get('file_type'),
            file_size=data.get('file_size'),
            width=data.get('width'),
            height=data.get('height'),
            duration=data.get('duration'),
            thumbnail_url=data.get('thumbnail_url'),
            created_at=created_at
        )
    
    def is_image(self) -> bool:
        """是否为图片"""
        return self.file_type == "image"
    
    def is_video(self) -> bool:
        """是否为视频"""
        return self.file_type == "video"
    
    def is_audio(self) -> bool:
        """是否为音频"""
        return self.file_type == "audio"
    
    def get_file_size_mb(self) -> float:
        """获取文件大小(MB)"""
        if self.file_size:
            return self.file_size / (1024 * 1024)
        return 0.0
    
    def get_duration_formatted(self) -> str:
        """获取格式化时长"""
        if not self.duration:
            return ""
        
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
@dataclass
class MessageVO:
    """消息视图对象"""
    message_id: str
    user_id: str
    username: str  # 发送者用户名
    content_type: str = "text"  # text/image/video/file/audio/system
    content: Optional[str] = None
    display_name: Optional[str] = None  # 发送者显示名称
    avatar_url: Optional[str] = None  # 发送者头像
    file_vo: Optional[FileVO] = None  # 如果是文件消息，包含文件信息
    is_edited: bool = False
    created_at: Optional[datetime] = None
    
    def is_text_message(self) -> bool:
        """是否为文本消息"""
        return self.content_type == "text"
    
    def is_file_message(self) -> bool:
        """是否为文件消息"""
        return self.content_type in ["image", "video", "file", "audio"]
    
    def is_system_message(self) -> bool:
        """是否为系统消息"""
        return self.content_type == "system"
    
    def get_formatted_time(self) -> str:
        """获取格式化时间"""
        if self.created_at:
            return self.created_at.strftime("%H:%M")
        return ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'user_id': self.user_id,
            'username': self.username,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'content_type': self.content_type,
            'content': self.content,
            'file_vo': self.file_vo.to_dict() if self.file_vo else None,
            'is_edited': self.is_edited,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageVO':
        """从字典创建MessageVO对象"""
        # 处理时间戳
        created_at = None
        if data.get('created_at'):
            try:
                created_at = datetime.fromisoformat(data['created_at'])
            except ValueError:
                pass
        
        # 处理文件VO（如果有）
        file_vo = None
        if data.get('file_vo'):
            file_vo = FileVO.from_dict(data['file_vo'])
        
        return cls(
            message_id=data.get('message_id', ''),
            user_id=data.get('user_id', ''),
            username=data.get('username', ''),
            content_type=data.get('content_type', 'text'),
            content=data.get('content'),
            display_name=data.get('display_name'),
            avatar_url=data.get('avatar_url'),
            file_vo=file_vo,
            is_edited=data.get('is_edited', False),
            created_at=created_at
        )


@dataclass
class PrivateMessageVO(MessageVO):
    """私聊消息视图对象"""
    conversation_id: str = ""
    sender_id: str = ""
    receiver_id: str = ""
    receiver_name: Optional[str] = None  # 接收者名称
    receiver_avatar: Optional[str] = None  # 接收者头像
    is_read: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'receiver_name': self.receiver_name,
            'receiver_avatar': self.receiver_avatar,
            'is_read': self.is_read
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PrivateMessageVO':
        """从字典创建PrivateMessageVO对象"""
        vo = cls()
        vo.message_id = data.get('message_id', '')
        vo.user_id = data.get('user_id', '')
        vo.username = data.get('username', '')
        vo.content = data.get('content', '')
        vo.content_type = data.get('content_type', 'text')
        vo.avatar_url = data.get('avatar_url', '')
        vo.conversation_id = data.get('conversation_id', '')
        vo.sender_id = data.get('sender_id', '')
        vo.receiver_id = data.get('receiver_id', '')
        vo.receiver_name = data.get('receiver', '') or data.get('receiver_name', '')
        vo.receiver_avatar = data.get('receiver_avatar', '')
        vo.is_read = data.get('is_read', False)
        
        # 处理时间戳
        created_at_str = data.get('created_at')
        vo.created_at = datetime.now()  # 默认值
        
        if created_at_str:
            try:
                if isinstance(created_at_str, str):
                    if len(created_at_str) == 8:  # HH:MM:SS格式
                        current_date = datetime.now().date()
                        parsed_time = datetime.strptime(created_at_str, '%H:%M:%S').time()
                        vo.created_at = datetime.combine(current_date, parsed_time)
                    elif created_at_str.isdigit():
                        vo.created_at = datetime.fromtimestamp(float(created_at_str))
                    else:
                        vo.created_at = datetime.fromisoformat(created_at_str)
                elif isinstance(created_at_str, datetime):
                    vo.created_at = created_at_str
            except Exception:
                vo.created_at = datetime.now()
        
        return vo


@dataclass
class ConversationVO:
    """会话视图对象"""
    conversation_id: str
    user1_id: str
    user2_id: str
    user1_name: str  # 用户1显示名称
    user2_name: str  # 用户2显示名称
    user1_avatar: Optional[str] = None  # 用户1头像
    user2_avatar: Optional[str] = None  # 用户2头像
    last_message_preview: Optional[str] = None  # 最后一条消息预览
    last_message_time: Optional[datetime] = None
    unread_count: int = 0  # 当前用户未读消息数
    is_muted: bool = False  # 当前用户是否静音该会话
    updated_at: Optional[datetime] = None
    
    def get_other_user_info(self, current_user_id: str) -> Dict[str, Any]:
        """获取对话方用户信息"""
        if current_user_id == self.user1_id:
            return {
                'user_id': self.user2_id,
                'username': self.user2_name,
                'avatar_url': self.user2_avatar
            }
        elif current_user_id == self.user2_id:
            return {
                'user_id': self.user1_id,
                'username': self.user1_name,
                'avatar_url': self.user1_avatar
            }
        return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'conversation_id': self.conversation_id,
            'user1_id': self.user1_id,
            'user2_id': self.user2_id,
            'user1_name': self.user1_name,
            'user2_name': self.user2_name,
            'user1_avatar': self.user1_avatar,
            'user2_avatar': self.user2_avatar,
            'last_message_preview': self.last_message_preview,
            'last_message_time': self.last_message_time.isoformat() if self.last_message_time else None,
            'unread_count': self.unread_count,
            'is_muted': self.is_muted,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class ChatRoomVO:
    """聊天室视图对象"""
    room_id: str
    room_name: str
    description: Optional[str] = None
    member_count: int = 0
    online_count: int = 0
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    is_public: bool = True
    avatar_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'room_id': self.room_id,
            'room_name': self.room_name,
            'description': self.description,
            'member_count': self.member_count,
            'online_count': self.online_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_public': self.is_public,
            'avatar_url': self.avatar_url
        }


@dataclass
class NotificationVO:
    """通知视图对象"""
    notification_id: str
    user_id: str
    title: str
    content: str
    is_read: bool = False
    created_at: Optional[datetime] = None
    related_entity_type: Optional[str] = None  # message, file, conversation等
    related_entity_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'notification_id': self.notification_id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'related_entity_type': self.related_entity_type,
            'related_entity_id': self.related_entity_id
        }
