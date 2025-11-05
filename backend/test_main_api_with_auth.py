#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试主API的认证功能
"""

import asyncio
import aiohttp
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_main_api():
    """测试主API的认证功能"""
    base_url = "http://localhost:8000"
    
    # 读取管理员token
    try:
        with open("admin_token.txt", "r") as f:
            admin_token = f.read().strip()
        logger.info("✅ 成功读取管理员token")
    except FileNotFoundError:
        logger.error("❌ 找不到admin_token.txt文件")
        return
    
    async with aiohttp.ClientSession() as session:
        try:
            logger.info("🚀 开始测试主API")
            
            # 测试1: 不带认证的请求（应该返回401）
            logger.info("🧪 测试1: 不带认证的请求")
            async with session.get(f"{base_url}/api/admin/users/") as response:
                logger.info(f"📊 状态码: {response.status}")
                if response.status == 401:
                    logger.info("✅ 正确返回401未授权")
                else:
                    logger.warning(f"⚠️ 预期401，实际返回{response.status}")
                    response_text = await response.text()
                    logger.info(f"响应内容: {response_text}")
            
            # 测试2: 带认证的请求（应该返回200）
            logger.info("\n🧪 测试2: 带认证的请求")
            headers = {"Authorization": f"Bearer {admin_token}"}
            async with session.get(f"{base_url}/api/admin/users/", headers=headers) as response:
                logger.info(f"📊 状态码: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ 成功获取用户列表")
                    
                    if 'data' in data:
                        logger.info(f"📊 总用户数: {data['data']['total']}")
                        logger.info(f"📄 当前页: {data['data']['page']}")
                        logger.info(f"📋 用户列表长度: {len(data['data']['users'])}")
                        
                        # 显示前3个用户的详细信息
                        for i, user in enumerate(data['data']['users'][:3]):
                            logger.info(f"  👤 用户{i+1}: ID={user['id']}, 用户名={user['username']}, 邮箱={user['email']}, 状态={user.get('status', '未知')}")
                    else:
                        logger.info(f"📄 响应数据: {data}")
                else:
                    logger.error(f"❌ 请求失败: {response.status}")
                    error_text = await response.text()
                    logger.error(f"错误信息: {error_text}")
            
            # 测试3: 测试分页功能
            logger.info("\n🧪 测试3: 测试分页功能")
            headers = {"Authorization": f"Bearer {admin_token}"}
            async with session.get(f"{base_url}/api/admin/users/?page=1&limit=5", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ 分页功能正常")
                    if 'data' in data:
                        logger.info(f"📊 分页结果: 第{data['data']['page']}页，共{data['data']['total']}个用户，当前页{len(data['data']['users'])}个")
                else:
                    logger.error(f"❌ 分页测试失败: {response.status}")
            
            # 测试4: 测试搜索功能
            logger.info("\n🧪 测试4: 测试搜索功能")
            headers = {"Authorization": f"Bearer {admin_token}"}
            async with session.get(f"{base_url}/api/admin/users/?search=test", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ 搜索功能正常")
                    if 'data' in data:
                        logger.info(f"📊 搜索结果: 找到{data['data']['total']}个包含'test'的用户")
                else:
                    logger.error(f"❌ 搜索测试失败: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_main_api())