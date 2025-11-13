#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全新的User模型 - 简化版本，确保分页功能正确
"""

import asyncio
import asyncpg
import json
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager

class NewUser:
    """全新的User模型类 - 简化版本"""
    
    def __init__(self, id: int = None, email: str = None, username: str = None, 
                 password_hash: str = None, is_active: bool = True, 
                 is_verified: bool = False, created_at: datetime = None, 
                 updated_at: datetime = None, last_login: datetime = None, 
                 login_count: int = 0, profile: Dict = None):
        self.id = id
        self.email = email
        self.username = username
        self.password_hash = password_hash
        self.is_active = is_active if is_active is not None else True
        self.is_verified = is_verified if is_verified is not None else False
        self.created_at = created_at
        self.updated_at = updated_at
        self.last_login = last_login
        self.login_count = login_count or 0
        self.profile = profile or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'profile': self.profile
        }
    
    @classmethod
    async def get_paginated_simple(cls, page: int = 1, limit: int = 20, 
                                  search: Optional[str] = None, 
                                  is_active: Optional[bool] = None) -> Tuple[List['NewUser'], int]:
        """
        获取分页用户列表 - 简化版本
        
        Args:
            page: 页码（从1开始）
            limit: 每页数量
            search: 搜索关键词（用户名或邮箱）
            is_active: 是否激活状态过滤
            
        Returns:
            Tuple[List[NewUser], int]: (用户列表, 总数)
        """
        print(f"🔍 开始获取用户列表 - 页码: {page}, 每页: {limit}, 搜索: {search}, 激活状态: {is_active}")
        
        # 计算偏移量
        offset = (page - 1) * limit
        
        # 构建基础查询
        base_query = """
            SELECT id, email, username, password_hash, is_active, is_verified,
                   created_at, updated_at, last_login, profile
            FROM users
        """
        
        count_query = "SELECT COUNT(*) FROM users"
        
        # 构建WHERE条件
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(email ILIKE $1 OR username ILIKE $2)")
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])
        
        if is_active is not None:
            param_index = len(params) + 1
            where_conditions.append(f"is_active = ${param_index}")
            params.append(is_active)
        
        # 组装完整查询
        where_clause = ""
        if where_conditions:
            where_clause = " WHERE " + " AND ".join(where_conditions)
        
        # 最终查询语句
        final_count_query = count_query + where_clause
        final_users_query = base_query + where_clause + f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        
        print(f"📊 总数查询: {final_count_query}")
        print(f"📋 用户查询: {final_users_query}")
        print(f"🔧 参数: {params + [limit, offset]}")
        
        # 获取数据库配置
        db_manager = DatabaseManager()
        config = db_manager.config
        
        try:
            # 连接数据库
            conn = await asyncpg.connect(**config)
            
            # 获取总数
            total_count = await conn.fetchval(final_count_query, *params)
            print(f"📈 总用户数: {total_count}")
            
            # 获取用户列表
            user_params = params + [limit, offset]
            results = await conn.fetch(final_users_query, *user_params)
            print(f"📋 查询到 {len(results)} 个用户")
            
            # 转换为User对象
            users = []
            for result in results:
                user = cls(
                    id=result['id'],
                    email=result['email'],
                    username=result['username'],
                    password_hash=result['password_hash'],
                    is_active=result['is_active'],
                    is_verified=result['is_verified'],
                    created_at=result['created_at'],
                    updated_at=result['updated_at'],
                    last_login=result['last_login'],
                    profile=json.loads(result['profile']) if result['profile'] else {}
                )
                users.append(user)
                print(f"  - 用户 {user.id}: {user.username} ({user.email})")
            
            await conn.close()
            
            print(f"✅ 成功返回 {len(users)} 个用户，总数: {total_count}")
            return users, total_count
            
        except Exception as e:
            print(f"❌ 获取用户列表时出错: {e}")
            import traceback
            traceback.print_exc()
            return [], 0

# 测试函数
async def test_new_user_model():
    """测试新的User模型"""
    print("=" * 80)
    print("🧪 测试新的User模型")
    print("=" * 80)
    
    # 测试1: 获取所有用户（第1页）
    print("\n📋 测试1: 获取所有用户（第1页，每页20条）")
    users, total = await NewUser.get_paginated_simple(page=1, limit=20)
    print(f"结果: {len(users)} 个用户，总数: {total}")
    
    # 测试2: 获取第1页，每页5条
    print("\n📋 测试2: 获取第1页，每页5条")
    users, total = await NewUser.get_paginated_simple(page=1, limit=5)
    print(f"结果: {len(users)} 个用户，总数: {total}")
    
    # 测试3: 获取第2页，每页5条
    print("\n📋 测试3: 获取第2页，每页5条")
    users, total = await NewUser.get_paginated_simple(page=2, limit=5)
    print(f"结果: {len(users)} 个用户，总数: {total}")
    
    # 测试4: 搜索功能
    print("\n📋 测试4: 搜索包含'test'的用户")
    users, total = await NewUser.get_paginated_simple(page=1, limit=20, search="test")
    print(f"结果: {len(users)} 个用户，总数: {total}")
    
    # 测试5: 过滤激活用户
    print("\n📋 测试5: 过滤激活用户")
    users, total = await NewUser.get_paginated_simple(page=1, limit=20, is_active=True)
    print(f"结果: {len(users)} 个用户，总数: {total}")

if __name__ == "__main__":
    asyncio.run(test_new_user_model())
