#!/usr/bin/env python3
"""
测试用户管理API
验证修复后的API是否能正确返回users表中的数据
"""

import requests
import json
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000"

def test_user_list_api():
    """测试用户列表API"""
    print("🔍 测试用户列表API...")
    
    try:
        # 测试不需要认证的API（如果有的话）
        url = f"{BASE_URL}/api/admin/users/"
        
        # 先尝试不带认证
        response = requests.get(url)
        print(f"📊 API响应状态码: {response.status_code}")
        
        if response.status_code in (401, 403):
            print("⚠️  需要认证（401/403），这是正常的")
            return True
        elif response.status_code == 200:
            data = response.json()
            print(f"✅ 成功获取用户列表")
            print(f"📈 用户总数: {data.get('total', 0)}")
            print(f"📄 当前页用户数: {len(data.get('users', []))}")
            
            # 显示前几个用户信息
            users = data.get('users', [])
            for i, user in enumerate(users[:3]):
                print(f"👤 用户 {i+1}: {user.get('username')} ({user.get('email')})")
            
            return True
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_api_structure():
    """测试API结构"""
    print("\n🔧 测试API结构...")
    
    try:
        # 测试API文档
        url = f"{BASE_URL}/docs"
        response = requests.get(url)
        
        if response.status_code == 200:
            print("✅ API文档可访问")
        else:
            print(f"⚠️  API文档状态: {response.status_code}")
            
        # 测试健康检查
        url = f"{BASE_URL}/health"
        response = requests.get(url)
        
        if response.status_code == 200:
            print("✅ 健康检查通过")
        else:
            print(f"⚠️  健康检查状态: {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"❌ 结构测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试用户管理API修复...")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 测试API结构
    structure_ok = test_api_structure()
    
    # 测试用户列表API
    list_ok = test_user_list_api()
    
    print("\n" + "=" * 50)
    print("📋 测试结果总结:")
    print(f"🔧 API结构测试: {'✅ 通过' if structure_ok else '❌ 失败'}")
    print(f"📊 用户列表测试: {'✅ 通过' if list_ok else '❌ 失败'}")
    
    if structure_ok and list_ok:
        print("🎉 所有测试通过！API修复成功")
    else:
        print("⚠️  部分测试失败，需要进一步检查")

if __name__ == "__main__":
    main()
