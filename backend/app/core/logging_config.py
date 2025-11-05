"""
JSON日志配置模块
提供生产环境下结构化日志输出，支持请求ID注入
"""

import logging
import json
from typing import Any, Dict
from contextvars import ContextVar


# 在上下文中存储请求ID，便于在日志中注入
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    """请求ID过滤器（函数级注释）
    从ContextVar读取请求ID并注入到日志记录的extra字段
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    """JSON日志格式化器（函数级注释）
    将日志记录格式化为结构化JSON，便于集中化日志平台解析
    """

    def format(self, record: logging.LogRecord) -> str:
        data: Dict[str, Any] = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record),
        }
        # 追加请求ID等上下文（如果存在）
        request_id = getattr(record, "request_id", None)
        if request_id:
            data["request_id"] = request_id
        return json.dumps(data, ensure_ascii=False)


def setup_logging(enable_json: bool = True) -> None:
    """初始化日志配置（函数级注释）
    当 enable_json 为 True 时启用JSON格式日志，否则使用默认格式
    """
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # 清理旧的handlers，避免重复添加
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    if enable_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(handler)

def set_request_id(request_id: str | None) -> None:
    """设置当前请求ID（函数级注释）
    在请求进入和完成时设置/清理请求ID用于日志注入
    """
    request_id_ctx.set(request_id)
