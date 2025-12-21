from functools import lru_cache

import yaml
import json
import os

from common.config.server.config_model import BaseServerConfig
from common.config.profile import Profile


@lru_cache()
def get_server_config(config_file="server/config.yaml") -> BaseServerConfig:
    """
    加载服务端配置
    :param config_file:
    :return:
    """

    project_root = Profile.get_project_root()

    config_path = project_root / config_file

    with open(config_path, "r", encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f)

    env_config = yaml_config.get("config", {})

    return BaseServerConfig(**env_config)