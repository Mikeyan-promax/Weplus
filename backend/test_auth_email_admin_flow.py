#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合测试：邮箱验证码注册流程 + 管理员登录流程
运行前确保后端已在 http://localhost:8000 启动
"""

import time
import json
import random
import string
import requests

BASE_URL = "http://localhost:8000"


def _rand_username(prefix: str = "u") -> str:
    """生成一个随机用户名（仅用于测试）"""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{suffix}"


def _rand_email(domain: str = "example.com") -> str:
    """生成一个随机邮箱地址（仅用于测试）"""
    ts = int(time.time())
    rnd = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"test_{ts}_{rnd}@{domain}"


def _pp(obj) -> str:
    """格式化为 JSON 字符串便于打印"""
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


def send_verification_code(email: str) -> str:
    """发送邮箱验证码并在DEBUG模式下读取回显的验证码

    返回：验证码字符串（如果DEBUG模式启用并且后端回显dev字段）
    抛出：RuntimeError 当请求失败或未获得验证码时
    """
    url = f"{BASE_URL}/api/auth/send-verification-code"
    resp = requests.post(url, json={"email": email})
    if resp.status_code != 200:
        raise RuntimeError(f"发送验证码失败: HTTP {resp.status_code} {resp.text}")
    data = resp.json()
    # 期望结构：{"success": true, ..., "dev": {"verification_code": "123456", ...}}
    dev = data.get("dev") or data.get("data", {}).get("dev")
    if not dev or "verification_code" not in dev:
        raise RuntimeError(f"未获取到调试回显验证码，响应={_pp(data)}")
    code = str(dev["verification_code"]).strip()
    if len(code) != 6 or not code.isdigit():
        raise RuntimeError(f"回显验证码格式不正确: {code}")
    return code


def register_user(email: str, username: str, password: str, code: str) -> dict:
    """使用验证码完成用户注册

    返回：注册成功后的响应JSON
    抛出：RuntimeError 当注册失败时
    """
    url = f"{BASE_URL}/api/auth/register"
    payload = {
        "email": email,
        "username": username,
        "password": password,
        "confirm_password": password,
        "verification_code": code,
    }
    resp = requests.post(url, json=payload)
    if resp.status_code != 200:
        raise RuntimeError(f"注册失败: HTTP {resp.status_code} {resp.text}")
    data = resp.json()
    if not data.get("success", False):
        raise RuntimeError(f"注册失败: {_pp(data)}")
    return data


def login_user(email: str, password: str) -> dict:
    """用户登录，返回令牌响应JSON"""
    url = f"{BASE_URL}/api/auth/login"
    resp = requests.post(url, json={"email": email, "password": password})
    if resp.status_code != 200:
        raise RuntimeError(f"登录失败: HTTP {resp.status_code} {resp.text}")
    data = resp.json()
    if not data.get("success", False):
        raise RuntimeError(f"登录失败: {_pp(data)}")
    return data


def admin_login(email: str = "admin@weplus.com", password: str = "admin123") -> dict:
    """管理员登录，返回令牌响应JSON"""
    url = f"{BASE_URL}/api/admin/auth/login"
    resp = requests.post(url, json={"email": email, "password": password})
    if resp.status_code != 200:
        raise RuntimeError(f"管理员登录失败: HTTP {resp.status_code} {resp.text}")
    data = resp.json()
    if not data.get("success", False):
        raise RuntimeError(f"管理员登录失败: {_pp(data)}")
    return data


def main():
    """主函数：串联执行验证码发送、注册、登录与管理员登录"""
    print("=== 综合测试：邮箱注册 + 管理员登录 ===")
    email = _rand_email()
    username = _rand_username()
    password = "P@ssw0rd123"

    print(f"1) 发送验证码到: {email}")
    code = send_verification_code(email)
    print(f"   ✅ 调试回显验证码: {code}")

    print(f"2) 使用验证码注册用户: {username}")
    reg = register_user(email, username, password, code)
    print(f"   ✅ 注册成功: {_pp(reg)}")

    print(f"3) 登录新注册用户: {email}")
    login = login_user(email, password)
    print(f"   ✅ 登录成功: 访问令牌前50位: {login.get('access_token','')[:50]}...")

    print("4) 管理员登录: admin@weplus.com")
    adm = admin_login()
    print(f"   ✅ 管理员登录成功: 访问令牌前50位: {adm.get('data',{}).get('access_token','')[:50]}...")

    print("\n🎉 全流程通过！")


if __name__ == "__main__":
    main()

