from typing import Dict
from pydantic_settings import BaseSettings

from common.config import get_server_config


class AppConfig(BaseSettings):
    name: str
    version: str
    description: str

class ServerConfig(BaseSettings):
    host: str
    port: int
    max_connections: int
    buffer_size: int

class SecurityConfig(BaseSettings):
    """安全配置"""
    password_salt: str

class UsersConfig(BaseSettings):
    valid_users: Dict[str, str]

class BaseServerConfig(BaseSettings):
    app: AppConfig
    server: ServerConfig
    security: SecurityConfig
    users: UsersConfig

server_config = get_server_config()