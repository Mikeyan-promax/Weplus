#!/usr/bin/env python3
"""
后端API全面巡检脚本（切库后验证）

功能概述：
- 读取管理员凭据，调用 /api/admin/auth/login 获取令牌；
- 对后台只读端点与主应用核心端点进行巡检（分页/搜索）；
- 输出每个端点的状态码、耗时与部分数据摘要；
- 当任一关键端点返回非200时，打印错误响应片段，便于定位。

使用说明：
- 需先启动后端：python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
- 默认基址：http://localhost:8000
- Windows多命令示例：
  python backend\\scripts\\full_api_smoke_test.py
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple

import aiohttp
import os
from datetime import datetime

BASE_URL = "http://localhost:8000"


async def _fetch_json(session: aiohttp.ClientSession, method: str, url: str,
                      headers: Optional[Dict[str, str]] = None,
                      params: Optional[Dict[str, Any]] = None,
                      json_body: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any], float, str]:
    """执行HTTP请求并返回状态码、JSON、耗时与错误文本

    参数：
    - method: 请求方法 GET/POST
    - url: 完整URL
    - headers: 请求头（可传入鉴权头）
    - params: 查询参数
    - json_body: JSON请求体
    返回：
    - (status, json_data, elapsed, error_text)
    """
    t0 = time.perf_counter()
    try:
        async with session.request(method, url, headers=headers, params=params, json=json_body) as resp:
            status = resp.status
            text = await resp.text()
            elapsed = time.perf_counter() - t0
            try:
                data = await resp.json()
            except Exception:
                data = {"raw": text[:500]}
            return status, data, elapsed, text
    except Exception as e:
        return 0, {"error": str(e)}, time.perf_counter() - t0, str(e)


async def _post_formdata(session: aiohttp.ClientSession, url: str,
                         fields: Dict[str, Any],
                         file_field_name: Optional[str] = None,
                         file_path: Optional[str] = None,
                         headers: Optional[Dict[str, str]] = None) -> Tuple[int, Dict[str, Any], float, str]:
    """提交multipart/form-data并返回状态码、JSON、耗时与错误文本

    函数级注释：
    - 用于文件上传等场景；
    - 支持可选文件字段（file_field_name + file_path）；
    - 返回四元组，便于统一日志打印。
    """
    t0 = time.perf_counter()
    try:
        form = aiohttp.FormData()
        # 添加普通字段
        for k, v in fields.items():
            form.add_field(k, str(v))
        # 添加文件字段
        if file_field_name and file_path and os.path.exists(file_path):
            fname = os.path.basename(file_path)
            # 基于扩展名推断内容类型，满足服务端对 file_type 的校验
            ext = os.path.splitext(fname)[1].lower()
            if ext == '.txt':
                content_type = 'text/plain'
            elif ext == '.md':
                content_type = 'text/markdown'
            elif ext == '.pdf':
                content_type = 'application/pdf'
            elif ext == '.png':
                content_type = 'image/png'
            elif ext in ('.jpg', '.jpeg'):
                content_type = 'image/jpeg'
            elif ext == '.zip':
                content_type = 'application/zip'
            else:
                content_type = 'application/octet-stream'
            with open(file_path, 'rb') as f:
                form.add_field(file_field_name, f, filename=fname, content_type=content_type)
                async with session.post(url, data=form, headers=headers or {}) as resp:
                    status = resp.status
                    text = await resp.text()
                    elapsed = time.perf_counter() - t0
                    try:
                        data = await resp.json()
                    except Exception:
                        data = {"raw": text[:500]}
                    return status, data, elapsed, text
        else:
            async with session.post(url, data=form, headers=headers or {}) as resp:
                status = resp.status
                text = await resp.text()
                elapsed = time.perf_counter() - t0
                try:
                    data = await resp.json()
                except Exception:
                    data = {"raw": text[:500]}
                return status, data, elapsed, text
    except Exception as e:
        return 0, {"error": str(e)}, time.perf_counter() - t0, str(e)


async def admin_login(session: aiohttp.ClientSession,
                      email: str = "admin@weplus.com",
                      password: str = "admin123") -> Optional[str]:
    """管理员登录，返回访问令牌（Bearer Token）"""
    status, data, elapsed, text = await _fetch_json(
        session, "POST", f"{BASE_URL}/api/admin/auth/login",
        json_body={"email": email, "password": password}
    )
    if status == 200 and data.get("success"):
        token = data.get("data", {}).get("access_token")
        return token
    print(f"[登录失败] status={status} 用时={elapsed:.3f}s 响应片段={text[:200]}")
    return None


async def rag_chat(session: aiohttp.ClientSession) -> Tuple[int, Dict[str, Any], float, str]:
    """调用RAG聊天端点（普通聊天模式）"""
    payload = {
        "message": "你好，来自巡检脚本的测试消息",
        "use_rag": False,
        "conversation_history": []
    }
    return await _fetch_json(session, "POST", f"{BASE_URL}/api/rag/chat", json_body=payload)


async def create_category(session: aiohttp.ClientSession) -> Tuple[int, Dict[str, Any], float, str]:
    """创建测试用学习资源分类，返回创建结果"""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    body = {
        "name": f"smoke_test_{ts}",
        "code": f"smoke_{ts}",
        "color": "#123456",
        "description": "巡检脚本自动创建分类"
    }
    return await _fetch_json(session, "POST", f"{BASE_URL}/api/study-resources/categories", json_body=body)


async def upload_resource(session: aiohttp.ClientSession, category_id: int) -> Tuple[int, Dict[str, Any], float, str]:
    """上传一个测试学习资源（普通端点），返回创建的资源信息"""
    test_file_candidates = [
        os.path.join("backend", "test_document_new.txt"),
        os.path.join("backend", "test_document.txt")
    ]
    file_path = next((p for p in test_file_candidates if os.path.exists(p)), None)
    fields = {
        "title": "巡检脚本测试资源",
        "description": "用于API巡检的测试文件",
        "category_id": category_id,
        "difficulty_level": "BEGINNER"
    }
    return await _post_formdata(session, f"{BASE_URL}/api/study-resources/upload", fields, "file", file_path)


async def admin_upload_resource(session: aiohttp.ClientSession, category_id: int, token: str) -> Tuple[int, Dict[str, Any], float, str]:
    """管理员上传测试资源，使用Bearer Token鉴权"""
    test_file_candidates = [
        os.path.join("backend", "test_document_new.txt"),
        os.path.join("backend", "test_document.txt")
    ]
    file_path = next((p for p in test_file_candidates if os.path.exists(p)), None)
    fields = {
        "title": "巡检脚本管理员上传资源",
        "description": "管理员端点测试上传",
        "category_id": category_id,
        "difficulty_level": "BEGINNER"
    }
    headers = {"Authorization": f"Bearer {token}"}
    return await _post_formdata(session, f"{BASE_URL}/api/study-resources/admin/upload", fields, "file", file_path, headers=headers)


async def rate_resource(session: aiohttp.ClientSession, resource_id: int) -> Tuple[int, Dict[str, Any], float, str]:
    """对资源进行评分，返回评分结果"""
    body = {
        "rating": 5,
        "comment": "巡检脚本评分：非常好",
        "user_id": 1
    }
    return await _fetch_json(session, "POST", f"{BASE_URL}/api/study-resources/{resource_id}/rate", json_body=body)


async def run_checks() -> None:
    """运行端到端巡检，包括管理员端点与主应用核心端点"""
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # 1) 管理员登录获取令牌
        print("\n[步骤1] 管理员登录以获取令牌...")
        token = await admin_login(session)
        if not token:
            print("❌ 无法获取管理员令牌，后续需要鉴权的端点将跳过")
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        # 2) 定义巡检清单（endpoint_name, path, method, requires_auth, params/json_body）
        print("\n[步骤2] 执行后台只读端点与主应用端点巡检...")
        checks: List[Dict[str, Any]] = [
            {"name": "测试中心-汇总", "method": "GET", "url": f"{BASE_URL}/api/test/summary", "auth": False},
            {"name": "仪表板-健康", "method": "GET", "url": f"{BASE_URL}/api/admin/dashboard/health", "auth": True},
            {"name": "仪表板-总览", "method": "GET", "url": f"{BASE_URL}/api/admin/dashboard/overview", "auth": True},
            {"name": "仪表板-完整数据", "method": "GET", "url": f"{BASE_URL}/api/admin/dashboard", "auth": True},
            {"name": "用户-分页(第1页,20)", "method": "GET", "url": f"{BASE_URL}/api/admin/users", "auth": True, "params": {"page": 1, "limit": 20}},
            {"name": "用户-分页(第1页,5)", "method": "GET", "url": f"{BASE_URL}/api/admin/users", "auth": True, "params": {"page": 1, "limit": 5}},
            {"name": "用户-搜索(test)", "method": "GET", "url": f"{BASE_URL}/api/admin/users", "auth": True, "params": {"search": "test"}},
            {"name": "RAG-统计", "method": "GET", "url": f"{BASE_URL}/api/admin/rag/stats", "auth": True},
            {"name": "RAG-文档列表(第1页,5)", "method": "GET", "url": f"{BASE_URL}/api/admin/rag/documents", "auth": True, "params": {"page": 1, "limit": 5}},
            {"name": "RAG-健康", "method": "GET", "url": f"{BASE_URL}/api/rag/health", "auth": False},
            {"name": "RAG-聊天(普通)", "method": "POST", "url": f"{BASE_URL}/api/rag/chat", "auth": False, "json": {"message": "你好，巡检脚本测试", "use_rag": False}},
            {"name": "向量DB-统计", "method": "GET", "url": f"{BASE_URL}/api/admin/vector/stats", "auth": True},
            {"name": "备份-列表", "method": "GET", "url": f"{BASE_URL}/api/admin/backup/list", "auth": True},
            {"name": "备份-健康", "method": "GET", "url": f"{BASE_URL}/api/admin/backup/health", "auth": True},
            {"name": "日志-表清单", "method": "GET", "url": f"{BASE_URL}/api/admin/logs/tables", "auth": True},
            {"name": "学习资源-分类", "method": "GET", "url": f"{BASE_URL}/api/study-resources/categories", "auth": False},
            {"name": "学习资源-列表", "method": "GET", "url": f"{BASE_URL}/api/study-resources/resources", "auth": False},
            {"name": "管理员-登出", "method": "POST", "url": f"{BASE_URL}/api/admin/auth/logout", "auth": False},
        ]

        ok_count = 0
        fail_items: List[str] = []

        for item in checks:
            name = item["name"]
            url = item["url"]
            method = item.get("method", "GET")
            needs_auth = item.get("auth", False)
            params = item.get("params")
            body = item.get("json")
            h = headers if (needs_auth and headers) else {}

            status, data, elapsed, text = await _fetch_json(session, method, url, headers=h, params=params, json_body=body)
            if status == 200:
                ok_count += 1
                # 简要摘要（若有data字段则打印部分统计）
                summary = []
                if isinstance(data, dict) and "data" in data:
                    d = data["data"]
                    if isinstance(d, dict):
                        if "total" in d: summary.append(f"total={d['total']}")
                        if "page" in d: summary.append(f"page={d['page']}")
                        if "users" in d and isinstance(d["users"], list): summary.append(f"users={len(d['users'])}")
                print(f"✅ {name} | 200 | {elapsed:.3f}s | {', '.join(summary) if summary else 'ok'}")
            else:
                fail_items.append(f"{name}({status})")
                print(f"❌ {name} | {status} | {elapsed:.3f}s | 错误片段: {text[:200]}")

        # 3) 动态操作：创建分类→上传资源→详情→评分→（可选）管理员上传
        print("\n[步骤3] 学习资源动态巡检（创建分类、上传、详情与评分）...")
        # 创建分类（失败则回退到获取已有分类）
        cat_status, cat_data, cat_elapsed, cat_text = await create_category(session)
        if cat_status == 200 and cat_data.get("success"):
            cat_id = (cat_data.get("data") or {}).get("id") or cat_data.get("id")
            print(f"✅ 分类创建 | 200 | {cat_elapsed:.3f}s | category_id={cat_id}")
        else:
            # 回退：获取已有分类列表，取第一个分类id
            print(f"❌ 分类创建 | {cat_status} | {cat_elapsed:.3f}s | 片段: {cat_text[:200]}")
            c_status, c_data, c_elapsed, c_text = await _fetch_json(session, "GET", f"{BASE_URL}/api/study-resources/categories")
            if c_status == 200 and c_data.get("success"):
                cats = c_data.get("data") or []
                cat_id = cats[0].get("id") if cats else None
                print(f"↪️ 回退使用已有分类 | {c_status} | {c_elapsed:.3f}s | category_id={cat_id}")
            else:
                cat_id = None
                print(f"❌ 获取已有分类失败 | {c_status} | {c_elapsed:.3f}s | 片段: {c_text[:200]}")

        res_id_for_ops = None
        if cat_id:
            up_status, up_data, up_elapsed, up_text = await upload_resource(session, cat_id)
            if up_status == 200 and up_data.get("success"):
                res = up_data.get("data") or {}
                res_id_for_ops = res.get("id") or res.get("resource_id")
                print(f"✅ 资源上传 | 200 | {up_elapsed:.3f}s | resource_id={res_id_for_ops}")
            else:
                print(f"❌ 资源上传 | {up_status} | {up_elapsed:.3f}s | 片段: {up_text[:200]}")

        # 获取详情并评分
        if res_id_for_ops:
            d_status, d_data, d_elapsed, d_text = await _fetch_json(session, "GET", f"{BASE_URL}/api/study-resources/{res_id_for_ops}")
            if d_status == 200 and d_data.get("success"):
                title = (d_data.get('data') or {}).get('title')
                print(f"✅ 资源详情 | 200 | {d_elapsed:.3f}s | title={title}")
            else:
                print(f"❌ 资源详情 | {d_status} | {d_elapsed:.3f}s | 片段: {d_text[:200]}")

            r_status, r_data, r_elapsed, r_text = await rate_resource(session, res_id_for_ops)
            if r_status == 200 and r_data.get("success"):
                print(f"✅ 资源评分 | 200 | {r_elapsed:.3f}s | ok")
            else:
                print(f"❌ 资源评分 | {r_status} | {r_elapsed:.3f}s | 片段: {r_text[:200]}")

        # 管理员上传（有令牌时）
        if token and cat_id:
            aup_status, aup_data, aup_elapsed, aup_text = await admin_upload_resource(session, cat_id, token)
            if aup_status == 200 and aup_data.get("success"):
                print(f"✅ 管理员资源上传 | 200 | {aup_elapsed:.3f}s | ok")
            else:
                print(f"❌ 管理员资源上传 | {aup_status} | {aup_elapsed:.3f}s | 片段: {aup_text[:200]}")

        print("\n[步骤4] 巡检总结：")
        print(f"通过：{ok_count}；失败：{len(fail_items)}")
        if fail_items:
            print("失败项：" + ", ".join(fail_items))


def main() -> None:
    """脚本入口：运行异步巡检流程"""
    asyncio.run(run_checks())


if __name__ == "__main__":
    main()
