# 导入客户端和服务端配置
from .client.config import get_client_config
from .server.config import get_server_config

__all__ = ['get_client_config', 'get_server_config']