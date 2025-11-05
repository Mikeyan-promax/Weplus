"""
IP级限流中间件
基于内存的滑动窗口计数，按分钟限制请求频率
"""

import time
from typing import Dict, Tuple, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简易IP限流中间件（函数级注释）
    使用内存字典记录每个IP的请求时间戳，超过阈值则返回429
    """

    def __init__(self, app: ASGIApp, enabled: bool, max_per_minute: int = 60) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.max_per_minute = max_per_minute
        self._store: Dict[str, list[float]] = {}

    async def dispatch(self, request, call_next: Callable):
        if not self.enabled:
            return await call_next(request)

        # 获取客户端IP（兼容反代）
        client_ip = request.headers.get("X-Forwarded-For", request.client.host)

        now = time.time()
        window_start = now - 60

        timestamps = self._store.setdefault(client_ip, [])
        # 滑动窗口：移除过期
        while timestamps and timestamps[0] < window_start:
            timestamps.pop(0)

        # 检查配额
        if len(timestamps) >= self.max_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Too Many Requests",
                    "limit_per_minute": self.max_per_minute,
                },
            )

        # 记录本次请求
        timestamps.append(now)
        return await call_next(request)

