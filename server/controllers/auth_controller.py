# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# 认证控制器
# 处理用户身份验证和授权
# """
# import asyncio
# from packaging.tags import android_platforms
# from sqlalchemy.ext.asyncio import AsyncEngine
#
# from common.config.server.config import get_server_config
# from common.database.crud.users_crud import user_crud
# from common.database.pg_helper import PgHelper
# from server.utils.password_utils import password_utils
# from common.log import log
#
# # 获取服务端配置
# server_config = get_server_config()
#
#
# class AuthController:
#     """
#     认证控制器类
#     负责处理用户登录认证和权限验证
#     """
#
#     @staticmethod
#     async def authenticate_user(db: AsyncEngine, username: str, password: str) -> bool:
#         """
#         用户认证（从数据库读取用户数据）
#
#         Args:
#             db: 异步引擎
#             username: 用户名
#             password: 密码
#
#         Returns:
#             bool: 认证成功返回True，否则返回False
#         """
#         if not username or not password:
#             return False
#
#         async with PgHelper.get_async_session(db) as session:
#             user = await user_crud.get_by_username(session, username)
#             # 修复：使用正确的字段名 password_hash 而不是 password
#             return user and password_utils.verify_password(password, user.password_hash)
#
#     @staticmethod
#     async def register_user(db: AsyncEngine, username: str, password: str, email: str = None, display_name: str = None) -> bool:
#         """
#         用户注册
#
#         Args:
#             db: 异步引擎
#             username: 用户名
#             password: 密码
#             email: 邮箱
#             display_name: 昵称
#
#         Returns:
#             bool: 注册成功返回True，否则返回False
#         """
#         if not username or not password:
#             return False
#
#         async with PgHelper.get_async_session(db) as session:
#             user = await user_crud.get_by_username(session, username)
#             if user:
#                 log.error(f"用户已存在: {username}")
#                 return False
#             log.info(f"注册用户: {username}")
#             await user_crud.create(
#                 session,
#                 username=username,
#                 password_hash=password_utils.hash_password(password),
#                 email=email,
#                 display_name=display_name if display_name else username
#             )
#             return True