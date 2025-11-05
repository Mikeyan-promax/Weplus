#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台只读端点巡检测试
覆盖管理员仪表板、用户管理、RAG、向量DB、备份、日志、测试中心与学习资源等只读接口，
旨在在部署前快速验证各模块的基本可用性与鉴权一致性。
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List


# 基础日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


async def admin_login(session: aiohttp.ClientSession) -> Optional[str]:
    """管理员登录以获取访问令牌"""
    url = f"{BASE_URL}/api/admin/auth/login"
    payload = {"email": "admin@weplus.com", "password": "admin123"}
    async with session.post(url, json=payload) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data.get("data", {}).get("access_token")
        text = await resp.text()
        logger.error(f"管理员登录失败: {resp.status} {text}")
        return None


async def get_json(session: aiohttp.ClientSession, url: str, headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    """GET 请求并尝试解析JSON，失败时返回错误结构"""
    try:
        async with session.get(url, headers=headers) as resp:
            status = resp.status
            try:
                data = await resp.json()
            except Exception:
                data = {"raw": await resp.text()}
            return {"status": status, "data": data}
    except Exception as e:
        return {"status": -1, "error": str(e)}


async def test_readonly_endpoints() -> None:
    """执行后台只读端点的巡检测试"""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        # 1) 管理员登录，准备鉴权头
        token = await admin_login(session)
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        # 2) 定义需要巡检的端点
        checks: List[tuple[str, str, bool]] = [
            ("测试中心-汇总", f"{BASE_URL}/api/test/summary", False),
            ("仪表板-健康", f"{BASE_URL}/api/admin/dashboard/health", True),
            ("仪表板-总览", f"{BASE_URL}/api/admin/dashboard/overview", True),
            ("仪表板-完整数据", f"{BASE_URL}/api/admin/dashboard", True),
            ("用户-分页", f"{BASE_URL}/api/admin/users?page=1&limit=5", True),
            ("RAG-统计", f"{BASE_URL}/api/admin/rag/stats", True),
            ("RAG-文档列表", f"{BASE_URL}/api/admin/rag/documents?page=1&limit=5", True),
            ("向量DB-统计", f"{BASE_URL}/api/admin/vector/stats", True),
            ("备份-列表", f"{BASE_URL}/api/admin/backup/list", True),
            ("备份-健康", f"{BASE_URL}/api/admin/backup/health", True),
            ("日志-表清单", f"{BASE_URL}/api/admin/logs/tables", True),
            ("学习资源-分类", f"{BASE_URL}/api/study-resources/categories", False),
            ("学习资源-列表", f"{BASE_URL}/api/study-resources/resources", False),
            ("文件-统计概览", f"{BASE_URL}/api/admin/files/stats/summary", True),
        ]

        # 3) 逐项请求并打印简要结果
        ok_count = 0
        for name, url, need_auth in checks:
            h = headers if need_auth else None
            result = await get_json(session, url, h)
            status = result.get("status")
            if status == 200:
                ok_count += 1
                logger.info(f"✅ {name} - 200 OK")
            else:
                logger.warning(f"⚠️  {name} - 状态码: {status} - 详情: {result.get('error') or result.get('data')}")

        logger.info(f"巡检完成：{ok_count}/{len(checks)} 项成功")


def main() -> None:
    """主入口：运行只读端点巡检"""
    logger.info("开始后台只读端点巡检测试…")
    asyncio.run(test_readonly_endpoints())


if __name__ == "__main__":
    main()

