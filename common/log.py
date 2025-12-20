import sys
from functools import lru_cache

from loguru import logger

from common.config.profile import Profile


class LogHelper:
    def __init__(self, log_file: str = "logs"):
        self.logger = logger

        self.logger.remove()

        project_root = Profile.get_project_root()
        log_file_path = project_root / log_file
        log_file_path.mkdir(parents=True, exist_ok=True)
        log_file_path = log_file_path / f"{log_file}.log"

        # 定义日志输出的基本格式
        formatter = (
            "<green>{time:YYYYMMDD HH:mm:ss}</green> | "
            "{process.name} | "
            "{thread.name} | "
            "<cyan>{module}</cyan>.<cyan>{function}</cyan> | "
            "<level>{level}</level> | "
            "{message}"
        )

        # 添加控制台输出 (default levels until config is loaded)
        self.logger.add(
            sink=sys.stdout,
            format=formatter,
            level="INFO",
        )

        # 添加文件输出 (default levels until config is loaded)
        self.logger.add(
            sink=log_file_path,
            format=formatter,
            level="DEBUG",
            rotation="500 MB",
            retention="10 days",
            encoding="utf-8"
        )

    @lru_cache()
    def get_logger(self):
        return self.logger


log_helper = LogHelper()
log = log_helper.get_logger()