#!/usr/bin/env python3
"""
前端页面导航测试脚本
测试管理员登录页面和学习资源管理页面的访问
"""

import requests
import time

def test_frontend_pages():
    """测试前端页面是否可访问"""
    frontend_url = "http://localhost:5173"
    
    print("🔍 测试前端页面访问...")
    
    try:
        # 测试主页
        response = requests.get(frontend_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ 前端主页访问成功: {frontend_url}")
        else:
            print(f"❌ 前端主页访问失败: {response.status_code}")
            
        # 测试管理员登录页面
        admin_login_url = f"{frontend_url}/admin/login"
        response = requests.get(admin_login_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ 管理员登录页面访问成功: {admin_login_url}")
        else:
            print(f"❌ 管理员登录页面访问失败: {response.status_code}")
            
        # 测试学习资源管理页面（需要登录，但可以测试路由）
        resources_url = f"{frontend_url}/admin/study-resources"
        response = requests.get(resources_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ 学习资源管理页面路由正常: {resources_url}")
        else:
            print(f"⚠️  学习资源管理页面状态: {response.status_code} (可能需要登录)")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到前端服务器，请确保前端服务器正在运行")
    except requests.exceptions.Timeout:
        print("❌ 请求超时，前端服务器可能响应缓慢")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

def test_backend_api():
    """测试后端API是否正常"""
    backend_url = "http://localhost:8000"
    
    print("\n🔍 测试后端API访问...")
    
    try:
        # 测试API健康检查
        response = requests.get(f"{backend_url}/", timeout=5)
        if response.status_code == 200:
            print(f"✅ 后端API访问成功: {backend_url}")
        else:
            print(f"❌ 后端API访问失败: {response.status_code}")
            
        # 测试管理员登录API
        login_url = f"{backend_url}/api/admin/auth/login"
        login_data = {
            "email": "admin@weplus.com",
            "password": "admin123"
        }
        response = requests.post(login_url, json=login_data, timeout=5)
        if response.status_code == 200:
            print(f"✅ 管理员登录API正常: {login_url}")
            token_data = response.json()
            print(f"🔍 API返回数据: {token_data}")
            if token_data.get("success") and token_data.get("data", {}).get("access_token"):
                print(f"✅ Token获取成功")
                return token_data["data"]["access_token"]
            elif "access_token" in token_data:
                print(f"✅ Token获取成功")
                return token_data["access_token"]
        else:
            print(f"❌ 管理员登录API失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务器，请确保后端服务器正在运行")
    except Exception as e:
        print(f"❌ 后端API测试出现错误: {e}")
    
    return None

def test_study_resources_api(token):
    """测试学习资源API"""
    if not token:
        print("⚠️  没有有效token，跳过学习资源API测试")
        return
        
    print("\n🔍 测试学习资源API...")
    
    try:
        api_url = "http://localhost:8000/api/study-resources/admin/resources"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{api_url}?page=1&page_size=10", headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"✅ 学习资源API调用成功")
            data = response.json()
            print(f"🔍 API返回数据结构: {type(data)}")
            if isinstance(data, dict) and data.get("success"):
                items = data.get('data', {})
                if isinstance(items, dict):
                    item_list = items.get('items', [])
                    print(f"✅ API返回数据正常，资源数量: {len(item_list)}")
                elif isinstance(items, list):
                    print(f"✅ API返回数据正常，资源数量: {len(items)}")
                else:
                    print(f"✅ API返回数据正常，数据类型: {type(items)}")
            else:
                print(f"⚠️  API返回数据: {data}")
        else:
            print(f"❌ 学习资源API调用失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 学习资源API测试出现错误: {e}")

if __name__ == "__main__":
    print("🚀 开始前端和后端集成测试...")
    print("=" * 50)
    
    # 测试前端页面
    test_frontend_pages()
    
    # 测试后端API并获取token
    token = test_backend_api()
    
    # 测试学习资源API
    test_study_resources_api(token)
    
    print("\n" + "=" * 50)
    print("✅ 测试完成！")
    print("\n💡 接下来请：")
    print("1. 打开浏览器访问 http://localhost:5173")
    print("2. 导航到管理员登录页面 /admin/login")
    print("3. 使用账号 admin / admin123 登录")
    print("4. 查看学习资源管理页面的TokenDebugger组件")
    print("5. 使用TokenDebugger测试API调用")