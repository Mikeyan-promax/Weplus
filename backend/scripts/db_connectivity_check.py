#!/usr/bin/env python3
"""
数据库连通性快速检查脚本

功能概述：
- 基于TCP层测试到指定PostgreSQL主机和端口的连通性；
- 基于psycopg2测试数据库会话可用性（执行 SELECT version()）；
- 自动读取后端 .env 的数据库配置（如未配置，使用新RDS默认值）。
"""

import os
import socket
from typing import Tuple
from urllib.parse import quote_plus

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


def load_env() -> None:
    """加载后端 .env 文件到环境变量中"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    env_path = os.path.abspath(env_path)
    if os.path.exists(env_path):
        load_dotenv(env_path)


def build_dsn(host: str, port: str, dbname: str, user: str, password: str) -> str:
    """构建 psycopg2 DSN 字符串（对密码进行URL编码避免特殊字符问题）"""
    password_encoded = quote_plus(password)
    return (
        f"host={host} port={port} dbname={dbname} user={user} "
        f"password={password_encoded} client_encoding=utf8"
    )


def test_tcp_connect(host: str, port: int, timeout: float = 3.0) -> Tuple[bool, str]:
    """测试到指定主机与端口的TCP连通性"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, "TCP连接成功"
    except Exception as e:
        return False, f"TCP连接失败: {e}"


def test_psql_connect(dsn: str) -> Tuple[bool, str]:
    """测试数据库会话可用性，执行 SELECT version()"""
    try:
        with psycopg2.connect(dsn) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT version() AS version")
                row = cursor.fetchone()
                return True, f"会话正常: {row['version']}"
    except Exception as e:
        return False, f"会话失败: {e}"


def main() -> None:
    """主流程：加载配置→测试新旧RDS连通性与会话"""
    load_env()

    # 读取环境变量（如不存在则使用新RDS默认）
    NEW_HOST = os.getenv('DB_HOST', 'pgm-2zekusmdjl0o3782ao.pg.rds.aliyuncs.com')
    PORT = int(os.getenv('DB_PORT', '5432'))
    DB_NAME = os.getenv('DB_NAME', 'weplus_db')
    USER = os.getenv('DB_USER', 'weplus_db')
    PASSWORD = os.getenv('DB_PASSWORD', '123456yzlA')

    OLD_HOST = 'pgm-2ze58b40mdfqec4zwo.pg.rds.aliyuncs.com'

    print("\n=== 新RDS TCP连通性测试 ===")
    ok, msg = test_tcp_connect(NEW_HOST, PORT)
    print(f"[{NEW_HOST}:{PORT}] {msg}")

    print("\n=== 旧RDS TCP连通性测试（参考） ===")
    ok_old, msg_old = test_tcp_connect(OLD_HOST, PORT)
    print(f"[{OLD_HOST}:{PORT}] {msg_old}")

    print("\n=== 新RDS 会话测试（psycopg2） ===")
    dsn_new = build_dsn(NEW_HOST, str(PORT), DB_NAME, USER, PASSWORD)
    ok2, msg2 = test_psql_connect(dsn_new)
    print(msg2)

    print("\n=== 旧RDS 会话测试（psycopg2，参考） ===")
    dsn_old = build_dsn(OLD_HOST, str(PORT), DB_NAME, USER, PASSWORD)
    ok3, msg3 = test_psql_connect(dsn_old)
    print(msg3)

    print("\n✅ 连通性测试完成")


if __name__ == "__main__":
    main()

