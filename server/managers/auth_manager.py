#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证管理器
负责用户认证和授权
"""

from common.database.pg_helper import PgHelper
from common.database.crud.users_crud import user_crud
from server.utils.password_utils import password_utils


class AuthManager:
    """认证管理器 - 负责所有认证相关的业务逻辑"""

    def __init__(self, db_engine):
        self.db_engine = db_engine

    async def authenticate(self, username: str, password: str) -> bool:
        """验证用户身份"""
        if not username or not password:
            return False

        try:
            async with PgHelper.get_async_session(self.db_engine) as session:
                user = await user_crud.get_by_username(session, username)
                return user and password_utils.verify_password(password, user.password_hash)

        except Exception:
            return False

    async def register(self, username: str, password: str,
                       email: str = None, display_name: str = None) -> bool:
        """注册新用户"""
        if not username or not password:
            return False

        try:
            async with PgHelper.get_async_session(self.db_engine) as session:
                # 检查用户是否已存在
                existing_user = await user_crud.get_by_username(session, username)
                if existing_user:
                    return False

                # 创建新用户
                await user_crud.create(
                    session,
                    username=username,
                    password_hash=password_utils.hash_password(password),
                    email=email,
                    display_name=display_name or username
                )

                return True

        except Exception:
            return False