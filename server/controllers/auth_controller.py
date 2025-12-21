#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证控制器
处理用户身份验证和授权
"""
from packaging.tags import android_platforms
from sqlalchemy.ext.asyncio import AsyncEngine

from common.config.config import config
from common.database.crud.users_crud import user_crud
from common.database.pg_helper import PgHelper
from server.utils.password_utils import password_utils


class AuthController:
    """
    认证控制器类
    负责处理用户登录认证和权限验证
    """
    
    @staticmethod
    async def authenticate_user(db: AsyncEngine, username: str, password: str) -> bool:
        """
        用户认证（从数据库读取用户数据）
        
        Args:
            db: 异步引擎
            username: 用户名
            password: 密码
            
        Returns:
            bool: 认证成功返回True，否则返回False
        """
        if not username or not password:
            return False

        session = PgHelper.get_async_session(db)

        user = await user_crud.get_by_username(session, username)
        return user and password_utils.verify_password(password, user.password)

        
