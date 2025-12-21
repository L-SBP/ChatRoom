#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
注册控制器
处理用户注册业务逻辑
"""

from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal

# 使用VO模型
from client.models.vo import UserVO
from client.network.network_manager import NetworkManager


class RegisterController(QObject):
    """注册控制器类"""

    # 信号定义
    register_success = pyqtSignal(str)  # 注册成功信号，参数为服务器返回的消息
    register_failed = pyqtSignal(str)  # 注册失败信号，参数为错误信息

    def __init__(self):
        super().__init__()
        # 使用网络管理器（单例模式）
        self.network_manager = NetworkManager()
        # 连接网络管理器的注册响应信号
        self.network_manager.register_response.connect(self.on_register_response)

    def register(self, username: str, password: str, email: str = "", nickname: str = "") -> bool:
        try:
            # 检查网络连接状态
            if not self.network_manager.connected:
                self.register_failed.emit("未连接到服务器，请检查网络连接")
                return False
                
            # 创建新用户VO
            user_vo = UserVO(
                user_id="",
                username=username,
                password=password,
                email=email,
                display_name=nickname if nickname else username,
                status="offline"
            )

            self.network_manager.register(user_vo)
            return True
        except Exception as e:
            self.register_failed.emit(f"注册失败: {str(e)}")
            return False
    
    def on_register_response(self, success: bool, message: str):
        """处理注册响应"""
        if success:
            self.register_success.emit(message)
        else:
            self.register_failed.emit(message)