"""
请求ID中间件
为每个HTTP请求注入唯一的请求ID，并与日志系统联动
"""

import uuid
from typing import Callable
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import set_request_id


class RequestIdMiddleware(BaseHTTPMiddleware):
    """请求ID中间件（函数级注释）
    从Header读取或生成请求ID，写入响应头，并注入到日志上下文
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request, call_next: Callable):
        # 读取或生成请求ID
        req_id = request.headers.get(self.header_name)
        if not req_id:
            req_id = str(uuid.uuid4())

        # 注入到日志上下文
        set_request_id(req_id)
        try:
            response = await call_next(request)
        finally:
            # 清理上下文，避免泄漏到其他请求
            set_request_id(None)

        # 将请求ID写入响应头
        response.headers[self.header_name] = req_id
        return response

