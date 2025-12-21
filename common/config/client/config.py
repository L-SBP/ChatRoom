from functools import lru_cache

import yaml
import json
import os

from common.config.client.config_model import BaseClientConfig
from common.config.profile import Profile


@lru_cache()
def get_client_config(config_file="client/config.yaml") -> BaseClientConfig:
    """
    加载客户端配置
    :param config_file:
    :return:
    """

    project_root = Profile.get_project_root()

    config_path = project_root / config_file

    with open(config_path, "r", encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f)

    env_config = yaml_config.get("config", {})

    return BaseClientConfig(**env_config)


def save_server_config(server_host: str, server_port: int):
    """
    保存服务器配置
    :param server_host:
    :param server_port:
    :return:
    """
    project_root = Profile.get_project_root()
    
    # 读取现有配置
    full_config_path = os.path.join(project_root, "client", "config.yaml")
    with open(full_config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    
    # 更新客户端配置
    if "client" not in config_data["config"]:
        config_data["config"]["client"] = {}
    config_data["config"]["client"]["default_server_host"] = server_host
    config_data["config"]["client"]["default_server_port"] = server_port
    
    # 保存配置
    with open(full_config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, allow_unicode=True, indent=2)