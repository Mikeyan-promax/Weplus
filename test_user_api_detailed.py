#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细测试用户管理API - 分析为什么只显示一个用户
"""

import requests
import json
from datetime import datetime

def test_admin_login():
    """测试管理员登录
    修正登录地址为 /api/admin/auth/login，并按返回结构解析token
    """
    print("🔐 步骤1: 管理员登录")
    
    login_data = {
        "email": "admin@weplus.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post("http://localhost:8000/api/admin/auth/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 登录成功")
            # 新接口返回 { success, data: { access_token, ... } }
            data = result.get("data", {}) if isinstance(result, dict) else {}
            return data.get("access_token")
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录出错: {e}")
        return None

def test_user_api_with_different_params(token):
    """测试不同参数下的用户API"""
    headers = {"Authorization": f"Bearer {token}"}
    
    test_cases = [
        {"name": "默认参数", "params": {}},
        {"name": "第1页，10条", "params": {"page": 1, "limit": 10}},
        {"name": "第1页，20条", "params": {"page": 1, "limit": 20}},
        {"name": "第1页，5条", "params": {"page": 1, "limit": 5}},
        {"name": "第2页，5条", "params": {"page": 2, "limit": 5}},
        {"name": "无搜索条件", "params": {"page": 1, "limit": 10, "search": ""}},
        {"name": "搜索test", "params": {"page": 1, "limit": 10, "search": "test"}},
        {"name": "搜索admin", "params": {"page": 1, "limit": 10, "search": "admin"}},
        {"name": "激活用户", "params": {"page": 1, "limit": 10, "is_active": True}},
        {"name": "未激活用户", "params": {"page": 1, "limit": 10, "is_active": False}},
    ]
    
    print(f"\n📊 步骤2: 测试不同参数组合")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. 测试: {test_case['name']}")
        print(f"   参数: {test_case['params']}")
        
        try:
            response = requests.get("http://localhost:8000/api/admin/users", 
                                  headers=headers, params=test_case['params'])
            
            if response.status_code == 200:
                result = response.json()
                
                # 分析响应结构
                print(f"   ✅ 请求成功")
                print(f"   📋 响应结构分析:")
                print(f"      - success: {result.get('success')}")
                print(f"      - message: {result.get('message')}")
                
                data = result.get('data', {})
                users = data.get('users', [])
                
                print(f"      - 用户数量: {len(users)}")
                print(f"      - 总用户数: {data.get('total', '未知')}")
                print(f"      - 当前页: {data.get('page', '未知')}")
                print(f"      - 每页数量: {data.get('limit', '未知')}")
                print(f"      - 总页数: {data.get('total_pages', '未知')}")
                
                # 显示用户详情
                if users:
                    print(f"   👥 用户列表:")
                    for j, user in enumerate(users, 1):
                        print(f"      {j}. ID: {user.get('id')}, 用户名: {user.get('username')}, 邮箱: {user.get('email')}")
                        print(f"         激活: {user.get('is_active')}, 验证: {user.get('is_verified')}")
                        print(f"         创建时间: {user.get('created_at')}")
                else:
                    print(f"   ⚠️ 没有返回用户数据")
                
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
                print(f"   响应内容: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 请求出错: {e}")
        
        print("   " + "-" * 60)

def test_direct_database_vs_api(token):
    """对比数据库直接查询和API结果"""
    print(f"\n🔍 步骤3: 对比数据库和API结果")
    
    # 从之前的数据库查询我们知道有9个用户
    expected_users = [
        {"id": 1, "username": "testuser_1761736746", "email": "testuser_1761736746@example.com"},
        {"id": 2, "username": "testuser_1761736746", "email": "testuser_1761736746@example.com"},
        {"id": 3, "username": "testuser_1761736746", "email": "testuser_1761736746@example.com"},
        {"id": 4, "username": "testuser_1761736746", "email": "testuser_1761736746@example.com"},
        {"id": 5, "username": "testuser_1761736746", "email": "testuser_1761736746@example.com"},
        {"id": 6, "username": "闫子凌", "email": "yanzilingwork@163.com"},
        {"id": 7, "username": "testuser_1761818513", "email": "testuser_1761818513@example.com"},
        {"id": 8, "username": "admin", "email": "admin@example.com"},
        {"id": 11, "username": "testuser", "email": "testuser@weplus.com"},
    ]
    
    print(f"📊 数据库中应该有的用户: {len(expected_users)} 个")
    for user in expected_users:
        print(f"   - ID: {user['id']}, 用户名: {user['username']}, 邮箱: {user['email']}")
    
    # 测试API
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get("http://localhost:8000/api/admin/users?page=1&limit=20", headers=headers)
        if response.status_code == 200:
            result = response.json()
            api_users = result.get('data', {}).get('users', [])
            
            print(f"\n📊 API返回的用户: {len(api_users)} 个")
            for user in api_users:
                print(f"   - ID: {user.get('id')}, 用户名: {user.get('username')}, 邮箱: {user.get('email')}")
            
            # 分析差异
            api_ids = {user.get('id') for user in api_users}
            expected_ids = {user['id'] for user in expected_users}
            
            missing_ids = expected_ids - api_ids
            extra_ids = api_ids - expected_ids
            
            if missing_ids:
                print(f"\n⚠️ API中缺失的用户ID: {missing_ids}")
            if extra_ids:
                print(f"\n⚠️ API中多出的用户ID: {extra_ids}")
            
            if len(api_users) == len(expected_users):
                print(f"\n✅ 用户数量匹配")
            else:
                print(f"\n❌ 用户数量不匹配: API返回{len(api_users)}个，期望{len(expected_users)}个")
                
        else:
            print(f"❌ API请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API测试出错: {e}")

def main():
    """主函数"""
    print("🔍 详细测试用户管理API")
    print("=" * 80)
    
    # 登录获取token
    token = test_admin_login()
    if not token:
        print("❌ 无法获取访问令牌，测试终止")
        return
    
    # 测试不同参数
    test_user_api_with_different_params(token)
    
    # 对比数据库和API结果
    test_direct_database_vs_api(token)
    
    print(f"\n✅ 测试完成")

if __name__ == "__main__":
    main()
