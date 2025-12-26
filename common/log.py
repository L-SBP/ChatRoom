# backend/app/core/log.py

import sys
import inspect
from loguru import logger

from common.config.profile import Profile

# 定义日志输出的基本格式
formatter = (
    "<green>{time:YYYYMMDD HH:mm:ss}</green> | "
    "{process.name} | "
    "{thread.name} | "
    "<cyan>{module}</cyan>.<cyan>{function}</cyan> | "
    "<level>{level}</level> | "
    "{message}"
)

# 确保日志目录存在
log_root = Profile.get_project_root() / "logs"
log_root.mkdir(parents=True, exist_ok=True)

# 清除所有现有的日志处理器
logger.remove()

# 添加控制台输出
logger.add(
    sink=sys.stdout,
    format=formatter,
    level="INFO"
)

# 创建客户端日志目录和文件
client_log_dir = log_root / "client"
client_log_dir.mkdir(exist_ok=True)

# 创建服务器日志目录和文件
server_log_dir = log_root / "server"
server_log_dir.mkdir(exist_ok=True)

# 添加客户端日志文件（使用过滤器）
logger.add(
    sink=client_log_dir / "client.log",
    format=formatter,
    level="DEBUG",
    rotation="500 MB",
    retention="10 days",
    encoding="utf-8",
    filter=lambda record: record["extra"].get("log_source") == "client"
)

# 添加服务器日志文件（使用过滤器）
logger.add(
    sink=server_log_dir / "server.log",
    format=formatter,
    level="DEBUG",
    rotation="500 MB",
    retention="10 days",
    encoding="utf-8",
    filter=lambda record: record["extra"].get("log_source") == "server"
)

# 根据调用上下文自动选择日志记录器
def get_logger():
    stack = inspect.stack()
    for frame_info in stack[1:]:
        module_path = frame_info.filename
        if "client/" in module_path:
            return logger.bind(log_source="client")
        elif "server/" in module_path:
            return logger.bind(log_source="server")
    return logger

# 创建并暴露客户端和服务器专用日志记录器
client_log = logger.bind(log_source="client")
server_log = logger.bind(log_source="server")

# 使用动态获取的日志记录器
log = get_logger()
