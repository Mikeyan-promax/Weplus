#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API导入问题
"""

import sys
import os

# 添加路径
sys.path.append(os.path.dirname(__file__))

try:
    print("🧪 测试导入 new_user_model...")
    from new_user_model import NewUser
    print("✅ 成功导入 NewUser")
    
    print("\n🧪 测试 NewUser.get_paginated_simple 方法...")
    import asyncio
    
    async def test_new_user():
        users, total = await NewUser.get_paginated_simple(page=1, limit=5)
        print(f"✅ 成功调用 get_paginated_simple: {len(users)} 个用户，总数: {total}")
        return users, total
    
    users, total = asyncio.run(test_new_user())
    
    print("\n🧪 测试用户转换为字典...")
    for i, user in enumerate(users[:2]):
        user_dict = user.to_dict()
        print(f"  👤 用户{i+1}: {user_dict['username']} ({user_dict['email']})")
    
    print("\n✅ 所有测试通过！")
    
except Exception as e:
    print(f"❌ 导入或测试失败: {e}")
    import traceback
    traceback.print_exc()