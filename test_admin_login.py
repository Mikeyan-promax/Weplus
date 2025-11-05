#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试管理员登录功能
"""

import requests
import json

def test_admin_login():
    """测试管理员登录API"""
    print("=== 测试管理员登录功能 ===")
    
    # 登录URL
    login_url = "http://localhost:8000/api/admin/auth/login"
    
    # 测试数据
    login_data = {
        "email": "admin@weplus.com",
        "password": "admin123"
    }
    
    try:
        print(f"正在测试登录API: {login_url}")
        print(f"登录数据: {login_data}")
        
        # 发送登录请求
        response = requests.post(login_url, json=login_data)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                token = result["data"]["access_token"]
                print(f"✅ 登录成功！")
                print(f"访问令牌: {token[:50]}...")
                return token
            else:
                print(f"❌ 登录失败: {result.get('message')}")
                return None
        else:
            print(f"❌ 登录请求失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 登录测试出错: {e}")
        return None

def test_user_list_with_token(token):
    """使用token测试用户列表API"""
    print("\n=== 测试用户列表API（带认证） ===")
    
    # 用户列表URL
    users_url = "http://localhost:8000/api/admin/users"
    
    # 请求头
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"正在测试用户列表API: {users_url}")
        print(f"使用认证头: Bearer {token[:20]}...")
        
        # 发送请求
        response = requests.get(users_url, headers=headers)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 用户列表API调用成功！")
            print(f"响应格式: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get("success") and "data" in result:
                users = result["data"]["users"]
                total = result["data"]["total"]
                print(f"📊 用户总数: {total}")
                print(f"📊 当前页用户数: {len(users)}")
                
                if users:
                    print("📋 用户列表预览:")
                    for i, user in enumerate(users[:3]):  # 只显示前3个用户
                        print(f"  {i+1}. ID: {user.get('id')}, 用户名: {user.get('username')}, 邮箱: {user.get('email')}")
                else:
                    print("📋 当前没有用户数据")
            else:
                print(f"⚠️ 响应格式异常: {result}")
        else:
            print(f"❌ 用户列表API调用失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 用户列表API测试出错: {e}")

def main():
    """主测试函数"""
    print("开始测试管理员登录和用户管理功能...")
    
    # 1. 测试管理员登录
    token = test_admin_login()
    
    if token:
        # 2. 使用token测试用户列表API
        test_user_list_with_token(token)
    else:
        print("❌ 无法获取有效token，跳过用户列表API测试")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()