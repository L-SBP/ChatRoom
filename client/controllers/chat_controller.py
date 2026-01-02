#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天控制器
处理聊天相关的业务逻辑
"""
import time
from typing import List, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime
import os

# 使用VO模型和网络管理器
from client.models.vo import MessageVO, FileVO, PrivateMessageVO
from client.network.network_manager import NetworkManager
from common.log import client_log as log


class ChatController(QObject):
    """聊天控制器类"""
    
    # 信号定义 - 使用VO对象（用于界面展示）
    connection_established = pyqtSignal()  # 连接建立成功
    connection_failed = pyqtSignal(str)    # 连接失败
    message_sent = pyqtSignal(object)     # 消息发送成功(VO对象)
    message_received = pyqtSignal(object) # 接收到消息(VO对象)
    user_list_updated = pyqtSignal(list)   # 用户列表更新
    file_sent = pyqtSignal(str)            # 文件发送成功
    file_received = pyqtSignal(str, str)   # 文件接收成功
    system_message = pyqtSignal(str)       # 系统消息
    
    def __init__(self):
        super().__init__()
        # 使用网络管理器（单例模式）
        self.network_manager = NetworkManager()
        self.network_manager.message_received.connect(self.on_message_received)
        self.network_manager.user_list_updated.connect(self.on_user_list_updated)
        self.network_manager.connection_status.connect(self.on_connection_status)
        self.network_manager.login_response.connect(self.on_login_response)
        self.network_manager.register_response.connect(self.on_register_response)
        self.network_manager.system_message.connect(self.on_system_message)
        
        # 用户列表
        self.online_users: List[str] = []
        self.current_user: str = ""
        self.connected: bool = False
        
        # 私聊窗口字典
        self.private_chat_windows = {}
        
        # 会话ID缓存，用于存储用户对之间的会话ID
        self.conversation_cache = {}

    def connect_to_server(self, server_host: str, server_port: int, username: str, password: str) -> bool:
        """连接到服务器"""
        # 连接服务器
        success = self.network_manager.connect_to_server(server_host, server_port)
        if success:
            # 登录
            self.network_manager.login(username, password)
            return True
        return False
    
    def use_existing_connection(self, username: str) -> bool:
        """使用现有连接"""
        if self.network_manager.is_connected():
            self.current_user = username
            self.connected = True
            self.connection_established.emit()
            # 获取用户列表
            self.refresh_user_list()
            return True
        return False
    
    def send_message(self, content: str) -> bool:
        """发送消息"""
        try:
            if not self.network_manager.is_connected():
                self.system_message.emit("未连接到服务器")
                return False
            
            if not content.strip():
                self.system_message.emit("消息内容不能为空")
                return False
            
            message_vo = MessageVO(
                message_id="",  # 会在服务端生成
                user_id="",     # 会在服务端设置
                username=self.current_user,
                content_type="text",
                content=content,
                created_at=datetime.now()
            )
            
            # 通过网络管理器发送消息
            success = self.network_manager.send_message(message_vo)
            if success:
                self.message_sent.emit(message_vo)
                log.debug(f"消息发送成功: {content}")
            else:
                self.system_message.emit("消息发送失败")
                log.error(f"消息发送失败: {content}")
            
            return success
        except Exception as e:
            log.error(f"发送消息时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def send_private_message(self, receiver: str, content: str, conversation_id: str = "") -> bool:
        """发送私聊消息"""
        try:
            if not self.network_manager.is_connected():
                self.system_message.emit("未连接到服务器")
                return False
            
            if not content.strip():
                self.system_message.emit("私聊消息内容不能为空")
                return False
            
            if not receiver:
                self.system_message.emit("请选择接收者")
                return False
            
            # 检查缓存中是否有会话ID
            if not conversation_id:
                conversation_key = f"{min(self.current_user, receiver)}_{max(self.current_user, receiver)}"
                conversation_id = self.conversation_cache.get(conversation_key, "")
            
            # 构造私聊消息数据
            data = {
                'type': 'private',
                'username': self.current_user,
                'receiver': receiver,
                'content': content,
                'content_type': 'text',
                'timestamp': datetime.now().timestamp()
            }
            
            # 如果有会话ID，添加到数据中
            if conversation_id:
                data['conversation_id'] = conversation_id
            
            # 创建私聊消息VO对象用于本地回显
            private_message_vo = PrivateMessageVO(
                message_id="",
                user_id="",
                username=self.current_user,
                receiver_name=receiver,
                content_type="text",
                content=content,
                conversation_id=conversation_id,
                created_at=datetime.now()
            )
            
            # 先发送消息到服务器
            self.network_manager.send_data(data)
            log.info(f"私聊消息已发送: {self.current_user} -> {receiver}, 内容: {content[:50]}..., 会话ID: {conversation_id}")
            
            # 不再立即在本地显示（回显），因为服务器会回传消息给发送者
            # self.message_sent.emit(private_message_vo)
            
            return True
        except Exception as e:
            log.error(f"发送私聊消息时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    def send_file(self, file_path: str) -> bool:
        """发送文件"""
        if not self.network_manager.is_connected():
            self.system_message.emit("未连接到服务器")
            return False

        success = self.network_manager.send_file(file_path)
        if success:
            self.file_sent.emit(os.path.basename(file_path))
        else:
            self.system_message.emit("文件发送失败")

        return success

    def send_voice(self, file_path: str) -> bool:
        """发送语音"""
        if not self.network_manager.is_connected():
            self.system_message.emit("未连接到服务器")
            return False

        success = self.network_manager.send_file(file_path)  # 复用send_file方法
        if success:
            self.file_sent.emit(os.path.basename(file_path))
        else:
            self.system_message.emit("语音发送失败")

        return success

    def send_image(self, file_path: str) -> bool:
        """发送图片"""
        log.debug(f"开始发送图片，文件路径: {file_path}")
        
        if not self.network_manager.is_connected():
            log.error("图片发送失败：未连接到服务器")
            self.system_message.emit("未连接到服务器")
            return False

        filename = os.path.basename(file_path)
        log.info(f"准备发送图片：{filename}")

        # 创建图片消息VO对象用于本地回显
        file_vo = FileVO(
            file_id="",
            file_name=filename,
            file_url=file_path,  # 使用本地文件路径
            file_type="image",
            file_size=os.path.getsize(file_path),
            created_at=datetime.now()
        )

        message_vo = MessageVO(
            message_id="",
            user_id="",
            username=self.current_user,
            content_type="image",
            content=filename,
            file_vo=file_vo,
            created_at=datetime.now()
        )

        # 立即在界面显示本地回显
        log.debug(f"发送本地图片回显：{filename}")
        self.message_sent.emit(message_vo)

        log.debug(f"调用network_manager.send_file发送图片：{filename}")
        success = self.network_manager.send_file(file_path)  # 复用send_file方法

        if success:
            log.info(f"图片发送成功：{filename}")
            self.file_sent.emit(filename)
        else:
            log.error(f"图片发送失败：{filename}")
            self.system_message.emit("图片发送失败")
            # 如果发送失败，可能需要从界面移除消息，但这里简单提示用户

        return success

    def send_video(self, file_path: str) -> bool:
        """发送视频"""
        if not self.network_manager.is_connected():
            self.system_message.emit("未连接到服务器")
            return False

        success = self.network_manager.send_file(file_path)  # 复用send_file方法
        if success:
            self.file_sent.emit(os.path.basename(file_path))
        else:
            self.system_message.emit("视频发送失败")

        return success
    
    def get_online_users(self) -> List[str]:
        """获取在线用户列表"""
        return self.online_users.copy()
    
    def start_private_chat(self, username: str) -> bool:
        """开始私聊"""
        if username == self.current_user:
            self.system_message.emit("不能与自己私聊")
            return False

        if username not in self.online_users:
            self.system_message.emit("用户不在线")
            return False

        # 这里可以启动私聊窗口，或者在视图层处理
        self.system_message.emit(f"开始与 {username} 私聊")
        return True
    
    def refresh_user_list(self):
        """刷新用户列表"""
        if not self.connected:
            self.system_message.emit("未连接到服务器")
            return

        # 通过网络管理器发送用户列表请求
        data = {'type': 'refresh_users'}
        self.network_manager.send_data(data)
    
    def get_history_messages(self, message_id: str = None, limit: int = 50) -> bool:
        """获取历史消息"""
        return self.network_manager.get_history_messages(message_id, limit)
    
    def get_private_history_messages(self, conversation_id: str, limit: int = 50) -> bool:
        """获取私聊历史消息"""
        try:
            if not self.network_manager.is_connected():
                self.system_message.emit("未连接到服务器")
                return False

            # 发送获取私聊历史消息的请求
            data = {
                'type': 'get_private_history',
                'conversation_id': conversation_id,
                'limit': limit
            }
            self.network_manager.send_data(data)
            return True
        except Exception as e:
            log.error(f"获取私聊历史消息时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_or_create_conversation(self, username1: str, username2: str) -> bool:
        """获取或创建私聊会话"""
        try:
            if not self.network_manager.is_connected():
                self.system_message.emit("未连接到服务器")
                return False

            # 发送获取或创建会话的请求
            data = {
                'type': 'get_conversation',
                'username1': username1,
                'username2': username2
            }
            self.network_manager.send_data(data)
            return True
        except Exception as e:
            log.error(f"获取或创建会话时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    def on_message_received(self, message_obj):
        """处理接收到的消息"""
        try:
            if isinstance(message_obj, list):
                # 历史消息列表
                for msg in message_obj:
                    # 判断是否为私聊消息
                    if hasattr(msg, 'content_type') and hasattr(msg, 'receiver_name') and hasattr(msg, 'conversation_id'):
                        # 私聊历史消息
                        self.message_received.emit(msg)
                    else:
                        # 普通历史消息
                        self.message_received.emit(msg)
                return

            # 检查是否为私聊消息
            if hasattr(message_obj, 'content_type') and hasattr(message_obj, 'receiver_name'):
                # 私聊消息
                self.message_received.emit(message_obj)
                return

            # 普通消息处理
            if hasattr(message_obj, 'content_type'):
                # VO对象
                self.message_received.emit(message_obj)
            elif isinstance(message_obj, dict):
                msg_type = message_obj.get('type', '')
                if msg_type == 'private':
                    # 处理私聊消息
                    # 处理私聊消息
                    # 注意：服务器发送的timestamp可能是时间字符串格式，需要特殊处理
                    timestamp_str = message_obj.get('timestamp', '')
                    created_at = datetime.now()  # 默认使用当前时间
                    
                    # 尝试将时间字符串解析为datetime对象
                    try:
                        # 检查是否为数字字符串（时间戳）
                        if isinstance(timestamp_str, (int, float)) or (isinstance(timestamp_str, str) and timestamp_str.isdigit()):
                            # 是时间戳格式
                            created_at = datetime.fromtimestamp(float(timestamp_str))
                        elif isinstance(timestamp_str, str) and len(timestamp_str) == 8:  # 假设是HH:MM:SS格式
                            # 是时间字符串格式，只包含时间部分
                            # 创建一个包含当前日期和解析到的时间的datetime对象
                            current_date = datetime.now().date()
                            parsed_time = datetime.strptime(timestamp_str, '%H:%M:%S').time()
                            created_at = datetime.combine(current_date, parsed_time)
                    except Exception as e:
                        log.error(f"解析时间戳失败: {e}, timestamp: {timestamp_str}")
                    
                    private_message_vo = PrivateMessageVO(
                        message_id=message_obj.get('message_id', ''),
                        user_id=message_obj.get('user_id', ''),
                        username=message_obj.get('username', ''),
                        receiver_name=message_obj.get('receiver', ''),
                        content_type=message_obj.get('content_type', 'text'),
                        content=message_obj.get('content', ''),
                        conversation_id=message_obj.get('conversation_id', ''),
                        created_at=created_at
                    )
                    # 如果是文件类型消息，添加文件信息
                    if message_obj.get('content_type') in ['image', 'video', 'file', 'audio']:
                        file_vo = FileVO(
                            file_name=message_obj.get('filename', ''),
                            file_url=message_obj.get('file_url', ''),
                            file_type=message_obj.get('content_type', 'file'),
                            file_size=message_obj.get('size', 0),
                            created_at=datetime.fromtimestamp(message_obj.get('timestamp', datetime.now().timestamp()))
                        )
                        private_message_vo.file_vo = file_vo

                    self.message_received.emit(private_message_vo)
                elif msg_type in ['text', 'image', 'video', 'file', 'audio', 'system']:
                    # 普通消息
                    message_vo = MessageVO.from_dict(message_obj)
                    self.message_received.emit(message_vo)
                elif msg_type == 'conversation_info':
                    # 会话信息响应
                    # 缓存会话ID
                    conversation_data = message_obj.get('conversation', {})
                    conversation_id = conversation_data.get('conversation_id', '')
                    user1_name = conversation_data.get('user1_name', '')
                    user2_name = conversation_data.get('user2_name', '')
                    
                    if conversation_id and user1_name and user2_name:
                        # 使用排序后的用户名作为键，确保一致性
                        conversation_key = f"{min(user1_name, user2_name)}_{max(user1_name, user2_name)}"
                        self.conversation_cache[conversation_key] = conversation_id
                        log.debug(f"缓存会话ID: {conversation_key} -> {conversation_id}")
                    
                    self.message_received.emit(message_obj)
                elif msg_type == 'private_history':
                    # 处理私聊历史消息
                    messages_data = message_obj.get('messages', [])
                    history_messages = []
                    for msg_data in messages_data:
                        # 转换为PrivateMessageVO对象
                        private_message_vo = PrivateMessageVO(
                            message_id=msg_data.get('message_id', ''),
                            user_id=msg_data.get('user_id', ''),
                            username=msg_data.get('username', ''),
                            receiver_name=msg_data.get('receiver', ''),
                            content_type=msg_data.get('content_type', 'text'),
                            content=msg_data.get('content', ''),
                            conversation_id=msg_data.get('conversation_id', ''),
                            created_at=datetime.fromisoformat(msg_data.get('timestamp', datetime.now().isoformat()))
                        )
                        history_messages.append(private_message_vo)
                    
                    # 发送历史消息列表
                    for msg in history_messages:
                        self.message_received.emit(msg)
                else:
                    log.error(f"未知的消息类型: {msg_type}")
            else:
                log.error(f"未知的消息格式: {type(message_obj)}")

        except Exception as e:
            log.error(f"处理接收到的消息时出错: {e}")
            import traceback
            traceback.print_exc()

    def on_user_list_updated(self, users: list):
        """处理用户列表更新"""
        self.online_users = users
        self.user_list_updated.emit(users)
        log.debug(f"用户列表更新: {users}")

    def on_connection_status(self, success: bool, message: str):
        """处理连接状态变化"""
        self.connected = success
        if success:
            self.connection_established.emit()
        else:
            self.connection_failed.emit(message)

    def on_login_response(self, success: bool, message: str):
        """处理登录响应"""
        if success:
            # 登录成功，设置当前用户
            self.connected = True
            self.connection_established.emit()
        else:
            self.connection_failed.emit(message)

    def on_register_response(self, success: bool, message: str):
        """处理注册响应"""
        if success:
            self.system_message.emit("注册成功")
        else:
            self.system_message.emit(f"注册失败: {message}")

    def on_system_message(self, message: str):
        """处理系统消息"""
        self.system_message.emit(message)