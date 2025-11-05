#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的用户管理API端点
"""

import asyncio
import aiohttp
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_api():
    """测试新的用户管理API"""
    base_url = "http://localhost:8000"
    
    # 通过管理员登录接口获取真实token
    # 函数：管理员登录并返回访问令牌
    async def admin_login() -> str:
        """调用 /api/admin/auth/login 获取管理员token"""
        login_payload = {"email": "admin@weplus.com", "password": "admin123"}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{base_url}/api/admin/auth/login", json=login_payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", {}).get("access_token")
                else:
                    txt = await resp.text()
                    logger.error(f"登录失败: {resp.status} {txt}")
                    return ""

    token = await admin_login()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} if token else {}
    
    async with aiohttp.ClientSession() as session:
        try:
            # 测试1: 获取所有用户（第1页）
            logger.info("🧪 测试1: 获取所有用户（第1页，每页20条）")
            async with session.get(
                f"{base_url}/api/admin/users/",
                params={"page": 1, "limit": 20},
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 成功获取用户列表")
                    logger.info(f"📊 总用户数: {data['data']['total']}")
                    logger.info(f"📄 当前页: {data['data']['page']}")
                    logger.info(f"📋 用户列表长度: {len(data['data']['users'])}")
                    
                    # 显示前3个用户的详细信息
                    for i, user in enumerate(data['data']['users'][:3]):
                        logger.info(f"  👤 用户{i+1}: ID={user['id']}, 用户名={user['username']}, 邮箱={user['email']}")
                else:
                    logger.error(f"❌ 请求失败: {response.status}")
                    error_text = await response.text()
                    logger.error(f"错误信息: {error_text}")
            
            # 测试2: 搜索用户
            logger.info("\n🧪 测试2: 搜索包含'test'的用户")
            async with session.get(
                f"{base_url}/api/admin/users/",
                params={"page": 1, "limit": 10, "search": "test"},
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 搜索成功")
                    logger.info(f"📊 搜索结果数量: {data['data']['total']}")
                    logger.info(f"📋 当前页用户数: {len(data['data']['users'])}")
                else:
                    logger.error(f"❌ 搜索失败: {response.status}")
            
            # 测试3: 过滤激活用户
            logger.info("\n🧪 测试3: 获取激活用户")
            async with session.get(
                f"{base_url}/api/admin/users/",
                params={"page": 1, "limit": 10, "is_active": True},
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 过滤成功")
                    logger.info(f"📊 激活用户数量: {data['data']['total']}")
                    logger.info(f"📋 当前页用户数: {len(data['data']['users'])}")
                else:
                    logger.error(f"❌ 过滤失败: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()

async def test_without_auth():
    """测试不带认证的API调用（应该失败）"""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        try:
            logger.info("\n🧪 测试4: 不带认证的API调用（应该返回401）")
            async with session.get(f"{base_url}/api/admin/users/") as response:
                logger.info(f"📊 响应状态码: {response.status}")
                if response.status == 401:
                    logger.info("✅ 正确返回401未授权错误")
                else:
                    logger.warning(f"⚠️ 预期401，但得到: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    logger.info("🚀 开始测试新的用户管理API")
    
    # 首先测试不带认证的调用
    asyncio.run(test_without_auth())
    
    # 然后测试带认证的调用（需要真实token）
    logger.info("\n⚠️ 注意: 带认证的测试需要真实的管理员token")
    logger.info("请先通过管理员账户登录获取token，然后更新test_api函数中的headers")
    
    # 如果你有真实的token，可以取消下面这行的注释
    # asyncio.run(test_api())
