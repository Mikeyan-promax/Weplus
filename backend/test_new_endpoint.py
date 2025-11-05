#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的API端点
"""

import asyncio
import aiohttp
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_new_api():
    """测试新的API端点（改为调用主服务 + 管理员鉴权）"""
    base_url = "http://localhost:8000"
    
    # 先获取管理员token
    async def admin_login() -> str:
        """通过 /api/admin/auth/login 获取管理员token"""
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{base_url}/api/admin/auth/login", json={"email":"admin@weplus.com","password":"admin123"}) as r:
                if r.status == 200:
                    d = await r.json()
                    return d.get("data", {}).get("access_token")
                else:
                    t = await r.text()
                    logger.error(f"管理员登录失败: {r.status} {t}")
                    return ""

    token = await admin_login()
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    async with aiohttp.ClientSession() as session:
        try:
            # 测试1: 获取所有用户（第1页）
            logger.info("🧪 测试1: 获取所有用户（第1页，每页20条）")
            async with session.get(f"{base_url}/api/admin/users?page=1&limit=20", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 成功获取用户列表")
                    logger.info(f"📄 响应数据结构: {list(data.keys())}")
                    logger.info(f"📄 完整响应: {data}")
                    
                    if 'data' in data:
                        logger.info(f"📊 总用户数: {data['data']['total']}")
                        logger.info(f"📄 当前页: {data['data']['page']}")
                        logger.info(f"📋 用户列表长度: {len(data['data']['users'])}")
                        
                        # 显示所有用户的详细信息
                        for i, user in enumerate(data['data']['users']):
                            logger.info(f"  👤 用户{i+1}: ID={user['id']}, 用户名={user['username']}, 邮箱={user['email']}, 激活={user['is_active']}")
                    else:
                        logger.error(f"❌ 响应中没有'data'字段")
                else:
                    logger.error(f"❌ 请求失败: {response.status}")
                    error_text = await response.text()
                    logger.error(f"错误信息: {error_text}")
            
            # 测试2: 搜索用户
            logger.info("\n🧪 测试2: 搜索包含'test'的用户")
            async with session.get(f"{base_url}/api/admin/users?page=1&limit=10&search=test", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 搜索成功")
                    logger.info(f"📊 搜索结果数量: {data['data']['total']}")
                    logger.info(f"📋 当前页用户数: {len(data['data']['users'])}")
                    
                    for i, user in enumerate(data['data']['users']):
                        logger.info(f"  🔍 搜索结果{i+1}: {user['username']} ({user['email']})")
                else:
                    logger.error(f"❌ 搜索失败: {response.status}")
            
            # 测试3: 过滤激活用户
            logger.info("\n🧪 测试3: 获取激活用户")
            async with session.get(f"{base_url}/api/admin/users?page=1&limit=10&is_active=true", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 过滤成功")
                    logger.info(f"📊 激活用户数量: {data['data']['total']}")
                    logger.info(f"📋 当前页用户数: {len(data['data']['users'])}")
                    
                    for i, user in enumerate(data['data']['users']):
                        logger.info(f"  ✅ 激活用户{i+1}: {user['username']} ({user['email']})")
                else:
                    logger.error(f"❌ 过滤失败: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    logger.info("🚀 开始测试新的API端点")
    asyncio.run(test_new_api())
