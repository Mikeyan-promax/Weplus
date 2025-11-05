#!/usr/bin/env python3
"""
测试学习资源API认证问题的脚本
"""

import requests
import json

def test_admin_login():
    """测试管理员登录"""
    print("🔐 测试管理员登录...")
    
    login_url = "http://localhost:8000/api/admin/auth/login"
    login_data = {
        "email": "admin@weplus.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        print(f"登录响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"登录成功: {data['success']}")
            if data['success']:
                token = data['data']['access_token']
                print(f"获取到token: {token[:50]}...")
                return token
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"登录请求异常: {e}")
        return None

def test_study_resources_api(token):
    """测试学习资源API"""
    print("\n📚 测试学习资源API...")
    
    api_url = "http://localhost:8000/api/study-resources/admin/resources"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {
        "page": 1,
        "page_size": 20
    }
    
    try:
        response = requests.get(api_url, headers=headers, params=params)
        print(f"API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API调用成功: {data['success']}")
            print(f"返回数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"API调用失败: {response.text}")
            
    except Exception as e:
        print(f"API请求异常: {e}")

def main():
    print("🚀 开始测试学习资源管理API认证...")
    
    # 1. 测试管理员登录
    token = test_admin_login()
    
    if token:
        # 2. 测试学习资源API
        test_study_resources_api(token)
    else:
        print("❌ 无法获取token，跳过API测试")
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    main()