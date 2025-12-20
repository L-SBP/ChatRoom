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

class ServerConfig(BaseSettings):
    host: str
    port: int
    max_connections: int
    buffer_size: int

class ClientConfig(BaseSettings):
    default_server_host: str
    default_server_port: int
    max_file_size: int
    timeout: int

class UsersConfig(BaseSettings):
    valid_users: Dict[str, str]

class BaseConfig(BaseSettings):
    app: AppConfig
    ui: UIConfig
    server: ServerConfig
    client: ClientConfig
    users: UsersConfig
