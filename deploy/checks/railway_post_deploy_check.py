#!/usr/bin/env python3
"""
Railway 发布后联通检查脚本（一次性巡检）

功能：对已部署的 WePlus 服务进行基础连通性验证，检查以下端点：
- /api/healthz（健康检查，对齐 Railway 配置）
- /health（基础健康检查，作为备用）
- /readyz（就绪检查，依赖简化）
- /docs（API 文档）

使用方法（Windows PowerShell）：
- 安装 Python 3.11+；在项目根目录执行：
  `python deploy/checks/railway_post_deploy_check.py --base-url https://<subdomain>.railway.app` 
- 可串联多个命令时使用 `;;`，例如：
  `python deploy/checks/railway_post_deploy_check.py --base-url https://xxx.railway.app ;; echo 完成`

注意：脚本仅进行 GET 请求，不会修改后端数据；若某些端点需要鉴权，脚本会跳过。
"""

import argparse
import json
import sys
import ssl
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def fetch_json(url: str, timeout: int = 8) -> dict:
    """执行 GET 请求并解析 JSON 响应
    参数：
    - url: 完整请求地址
    - timeout: 超时时间（秒）
    返回：
    - 若成功，返回字典；若失败，返回包含 error 字段的字典
    """
    try:
        # 创建请求对象，增加基础头部
        req = Request(url, headers={"User-Agent": "WePlus-Post-Deploy-Check/1.0"})
        # 兼容部分平台的证书握手问题
        ctx = ssl.create_default_context()
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            data = resp.read().decode("utf-8", errors="ignore")
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return {"error": "非JSON响应", "raw": data[:200]}
    except HTTPError as e:
        return {"error": f"HTTP错误: {e.code}", "detail": e.reason}
    except URLError as e:
        return {"error": f"连接错误: {e.reason}"}
    except Exception as e:
        return {"error": f"未知错误: {str(e)}"}


def check_endpoint(base: str, path: str) -> tuple[int, dict]:
    """检查指定端点并返回状态码与数据
    参数：
    - base: 基础地址（例如 https://xxx.railway.app）
    - path: 端点路径（例如 /api/healthz）
    返回：
    - (status, data) 二元组；status 为 200 表示成功
    """
    url = f"{base.rstrip('/')}{path}"
    result = fetch_json(url)
    if isinstance(result, dict) and "error" not in result:
        return 200, result
    return 500, result


def main() -> int:
    """主入口：解析参数并依次执行检查，打印简要结果"""
    parser = argparse.ArgumentParser(description="WePlus Railway 发布后联通检查")
    parser.add_argument("--base-url", required=True, help="Railway 分配的公共域名，如 https://xxx.railway.app")
    args = parser.parse_args()

    base = args.base_url
    print(f"🔍 开始检查：{base}")

    checks = [
        ("健康检查", "/api/healthz"),
        ("备用健康", "/health"),
        ("就绪检查", "/readyz"),
        ("API文档", "/docs"),
    ]

    ok = 0
    for name, path in checks:
        status, data = check_endpoint(base, path)
        if status == 200:
            ok += 1
            print(f"✅ {name} - 200 OK | {path} | 响应: {str(data)[:120]}")
        else:
            print(f"⚠️  {name} - 非200 | {path} | 详情: {data}")

    print(f"\n📊 巡检完成：{ok}/{len(checks)} 项通过")
    return 0 if ok >= 2 else 1


if __name__ == "__main__":
    sys.exit(main())

