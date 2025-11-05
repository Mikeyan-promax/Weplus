"""
管理端IP白名单依赖
用于保护 /api/admin* 路由在生产环境下仅允许指定来源访问
"""

from typing import List
from fastapi import Request, HTTPException, status

from app.core.config import settings


async def require_admin_ip_whitelist(request: Request) -> None:
    """校验管理员端请求来源IP（函数级注释）
    读取 X-Forwarded-For 或客户端IP，与配置中的白名单比对
    """
    whitelist: List[str] = settings.ADMIN_IP_WHITELIST or []
    # 默认允许本地开发
    if not whitelist:
        return

    # 读取真实IP（兼容反向代理场景）
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    # 仅取第一个
    if isinstance(client_ip, str) and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    if client_ip not in whitelist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Admin access denied for IP: {client_ip}",
        )

