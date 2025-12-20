#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模型类
定义配置数据结构和管理
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import json
import os


@dataclass
class AppConfig:
    """应用配置"""
    name: str = "ChatRoom"
    version: str = "1.0.0"
    description: str = "A simple chat room"


@dataclass
class FontConfig:
    """字体配置"""
    family: str = "Microsoft YaHei, PingFang SC, WenQuanYi Micro Hei, SimHei, Arial"
    titleSize: int = 20
    subtitleSize: int = 14
    normalSize: int = 12


@dataclass
class UIConfig:
    """UI配置"""
    windowWidth: int = 1300
    windowHeight: int = 750
    windowTitle: str = "Chat Room"
    windowIcon: str = "icon.png"
    windowBackgroundColor: str = "#FFFFFF"
    font: FontConfig = None
    
    def __post_init__(self):
        if self.font is None:
            self.font = FontConfig()


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8888
    max_connections: int = 100
    buffer_size: int = 1024


@dataclass
class ClientConfig:
    """客户端配置"""
    default_server_host: str = "127.0.0.1"
    default_server_port: int = 8888
    max_file_size: int = 10485760  # 10MB
    timeout: int = 10


@dataclass
class UsersConfig:
    """用户配置"""
    valid_users: Dict[str, str] = None
    
    def __post_init__(self):
        if self.valid_users is None:
            self.valid_users = {
                'admin': '123456',
                'user1': '123456',
                'user2': '123456',
                'test': '123456'
            }


@dataclass
class BaseConfig:
    """基础配置类"""
    app: AppConfig = None
    ui: UIConfig = None
    server: ServerConfig = None
    client: ClientConfig = None
    users: UsersConfig = None
    
    def __post_init__(self):
        if self.app is None:
            self.app = AppConfig()
        if self.ui is None:
            self.ui = UIConfig()
        if self.server is None:
            self.server = ServerConfig()
        if self.client is None:
            self.client = ClientConfig()
        if self.users is None:
            self.users = UsersConfig()
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'app': {
                'name': self.app.name,
                'version': self.app.version,
                'description': self.app.description
            },
            'ui': {
                'windowWidth': self.ui.windowWidth,
                'windowHeight': self.ui.windowHeight,
                'windowTitle': self.ui.windowTitle,
                'windowIcon': self.ui.windowIcon,
                'windowBackgroundColor': self.ui.windowBackgroundColor
            },
            'server': {
                'host': self.server.host,
                'port': self.server.port,
                'max_connections': self.server.max_connections,
                'buffer_size': self.server.buffer_size
            },
            'client': {
                'default_server_host': self.client.default_server_host,
                'default_server_port': self.client.default_server_port,
                'max_file_size': self.client.max_file_size,
                'timeout': self.client.timeout
            },
            'users': {
                'valid_users': self.users.valid_users
            }
        }
    
    def to_json(self) -> str:
        """转换为JSON格式"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    def save_to_file(self, filepath: str) -> bool:
        """保存配置到文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str) -> Optional['BaseConfig']:
        """从文件加载配置"""
        try:
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 构建配置对象
            app_config = AppConfig(
                name=data.get('app', {}).get('name', 'ChatRoom'),
                version=data.get('app', {}).get('version', '1.0.0'),
                description=data.get('app', {}).get('description', 'A simple chat room')
            )
            
            ui_font_config = None
            ui_font_data = data.get('ui', {}).get('font', {})
            if ui_font_data:
                ui_font_config = FontConfig(
                    family=ui_font_data.get('family', 'Microsoft YaHei, PingFang SC, WenQuanYi Micro Hei, SimHei, Arial'),
                    titleSize=ui_font_data.get('titleSize', 20),
                    subtitleSize=ui_font_data.get('subtitleSize', 14),
                    normalSize=ui_font_data.get('normalSize', 12)
                )
            
            ui_config = UIConfig(
                windowWidth=data.get('ui', {}).get('windowWidth', 1300),
                windowHeight=data.get('ui', {}).get('windowHeight', 750),
                windowTitle=data.get('ui', {}).get('windowTitle', 'Chat Room'),
                windowIcon=data.get('ui', {}).get('windowIcon', 'icon.png'),
                windowBackgroundColor=data.get('ui', {}).get('windowBackgroundColor', '#FFFFFF'),
                font=ui_font_config
            )
            
            server_config = ServerConfig(
                host=data.get('server', {}).get('host', '0.0.0.0'),
                port=data.get('server', {}).get('port', 8888),
                max_connections=data.get('server', {}).get('max_connections', 100),
                buffer_size=data.get('server', {}).get('buffer_size', 1024)
            )
            
            client_config = ClientConfig(
                default_server_host=data.get('client', {}).get('default_server_host', '127.0.0.1'),
                default_server_port=data.get('client', {}).get('default_server_port', 8888),
                max_file_size=data.get('client', {}).get('max_file_size', 10485760),
                timeout=data.get('client', {}).get('timeout', 10)
            )
            
            users_config = UsersConfig(
                valid_users=data.get('users', {}).get('valid_users', {})
            )
            
            return cls(
                app=app_config,
                ui=ui_config,
                server=server_config,
                client=client_config,
                users=users_config
            )
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return None


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self.config: Optional[BaseConfig] = None
        self.load_config()
    
    def load_config(self) -> bool:
        """加载配置"""
        # 尝试从YAML文件加载
        try:
            import yaml
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    yaml_data = yaml.safe_load(f)
                config_data = yaml_data.get('config', {})
                
                # 构建配置对象
                self.config = BaseConfig(
                    app=AppConfig(
                        name=config_data.get('app', {}).get('name', 'ChatRoom'),
                        version=config_data.get('app', {}).get('version', '1.0.0'),
                        description=config_data.get('app', {}).get('description', 'A simple chat room')
                    ),
                    ui=UIConfig(
                        windowWidth=config_data.get('ui', {}).get('windowWidth', 1300),
                        windowHeight=config_data.get('ui', {}).get('windowHeight', 750),
                        windowTitle=config_data.get('ui', {}).get('windowTitle', 'Chat Room'),
                        windowIcon=config_data.get('ui', {}).get('windowIcon', 'icon.png'),
                        windowBackgroundColor=config_data.get('ui', {}).get('windowBackgroundColor', '#FFFFFF')
                    ),
                    server=ServerConfig(
                        host=config_data.get('server', {}).get('host', '0.0.0.0'),
                        port=config_data.get('server', {}).get('port', 8888),
                        max_connections=config_data.get('server', {}).get('max_connections', 100),
                        buffer_size=config_data.get('server', {}).get('buffer_size', 1024)
                    ),
                    client=ClientConfig(
                        default_server_host=config_data.get('client', {}).get('default_server_host', '127.0.0.1'),
                        default_server_port=config_data.get('client', {}).get('default_server_port', 8888),
                        max_file_size=config_data.get('client', {}).get('max_file_size', 10485760),
                        timeout=config_data.get('client', {}).get('timeout', 10)
                    ),
                    users=UsersConfig(
                        valid_users=config_data.get('users', {}).get('valid_users', {})
                    )
                )
                return True
        except ImportError:
            print("未安装PyYAML，请安装: pip install pyyaml")
        except Exception as e:
            print(f"加载YAML配置失败: {e}")
        
        # 尝试从JSON文件加载
        json_file = self.config_file.replace('.yaml', '.json').replace('.yml', '.json')
        if os.path.exists(json_file):
            self.config = BaseConfig.load_from_file(json_file)
            return self.config is not None
        
        # 使用默认配置
        self.config = BaseConfig()
        return True
    
    def save_config(self) -> bool:
        """保存配置"""
        if self.config:
            return self.config.save_to_file(self.config_file.replace('.yaml', '.json').replace('.yml', '.json'))
        return False
    
    def get_config(self) -> Optional[BaseConfig]:
        """获取配置对象"""
        return self.config
    
    def update_config(self, new_config: BaseConfig) -> None:
        """更新配置"""
        self.config = new_config
        self.save_config()
