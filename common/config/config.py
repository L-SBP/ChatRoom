from functools import lru_cache

import yaml

from common.config.config_model import BaseConfig
from common.config.profile import Profile


@lru_cache()
def get_config(config_file="config.yaml") -> BaseConfig :
    """
    加载配置
    :param config_file:
    :return:
    """

    project_root = Profile.get_project_root()

    config_path = project_root / config_file

    with open(config_path, "r", encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f)

    env_config = yaml_config.get("config", {})

    return BaseConfig(**env_config)

config = get_config()