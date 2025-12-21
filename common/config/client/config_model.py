from typing import Dict
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    name: str
    version: str
    description: str

class FontConfig(BaseSettings):
    family: str
    titleSize: int
    subtitleSize: int
    normalSize: int

class UIConfig(BaseSettings):
    windowWidth: int
    windowHeight: int
    minWindowWidth: int
    minWindowHeight: int
    windowTitle: str
    windowIcon: str
    windowBackgroundColor: str
    font: FontConfig

class ClientConfig(BaseSettings):
    default_server_host: str
    default_server_port: int
    max_file_size: int
    timeout: int

class SecurityConfig(BaseSettings):
    """安全配置"""
    password_salt: str

class BaseClientConfig(BaseSettings):
    app: AppConfig
    ui: UIConfig
    client: ClientConfig
    security: SecurityConfig