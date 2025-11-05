#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细测试新的用户管理API端点
"""

import asyncio
import aiohttp
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_api_detailed():
    """详细测试API响应"""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        try:
            logger.info("🧪 测试: 不带认证直接调用用户管理API")
            async with session.get(f"{base_url}/api/admin/users/") as response:
                logger.info(f"📊 响应状态码: {response.status}")
                logger.info(f"📋 响应头: {dict(response.headers)}")
                
                response_text = await response.text()
                logger.info(f"📄 响应内容长度: {len(response_text)}")
                
                try:
                    response_json = json.loads(response_text)
                    logger.info(f"✅ JSON响应解析成功")
                    logger.info(f"📊 响应结构: {list(response_json.keys())}")
                    
                    if 'data' in response_json:
                        data = response_json['data']
                        logger.info(f"📋 数据字段: {list(data.keys())}")
                        if 'users' in data:
                            logger.info(f"👥 用户数量: {len(data['users'])}")
                            logger.info(f"📊 总用户数: {data.get('total', 'N/A')}")
                            
                            # 显示前3个用户
                            for i, user in enumerate(data['users'][:3]):
                                logger.info(f"  👤 用户{i+1}: ID={user.get('id')}, 用户名={user.get('username')}, 邮箱={user.get('email')}")
                    
                    if 'success' in response_json:
                        logger.info(f"✅ 成功状态: {response_json['success']}")
                    
                    if 'message' in response_json:
                        logger.info(f"💬 消息: {response_json['message']}")
                        
                except json.JSONDecodeError:
                    logger.error("❌ 响应不是有效的JSON")
                    logger.info(f"📄 原始响应内容: {response_text[:500]}...")
                    
        except Exception as e:
            logger.error(f"❌ 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    logger.info("🚀 开始详细测试用户管理API")
    asyncio.run(test_api_detailed())