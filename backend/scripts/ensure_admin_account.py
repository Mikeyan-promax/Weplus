#!/usr/bin/env python3
"""
确保新数据库存在管理员账户 admin@weplus.com / admin123

功能概述：
- 读取 .env 配置连接到新RDS；
- 检查旧RDS是否已存在该管理员（仅调研用）；
- 如新RDS不存在，则创建管理员为 super_admin、已验证；
- 使用bcrypt安全哈希密码，兼容现有验证逻辑。
"""

import os
from typing import Optional
from urllib.parse import quote_plus

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import bcrypt


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


def connect(dsn: str):
    """建立数据库连接，返回连接对象"""
    return psycopg2.connect(dsn)


def admin_exists(conn, email: str = "admin@weplus.com") -> bool:
    """检查 admin_users 表中是否存在指定管理员邮箱"""
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT id, email, username FROM admin_users WHERE email = %s", (email,))
        return cursor.fetchone() is not None


def create_admin(conn,
                 email: str = "admin@weplus.com",
                 username: str = "admin",
                 plain_password: str = "admin123") -> Optional[int]:
    """在新库创建管理员账号（幂等前置，需确保不存在；若缺表则创建）"""
    # 若表不存在，先创建基础结构（与 init_postgresql.py 保持一致）
    with conn.cursor() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(100) UNIQUE NOT NULL,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin', 'super_admin')),
                is_active BOOLEAN DEFAULT TRUE,
                is_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                login_count INTEGER DEFAULT 0,
                real_name VARCHAR(100) DEFAULT '',
                phone VARCHAR(20) DEFAULT '',
                department VARCHAR(100) DEFAULT '',
                student_id VARCHAR(50) DEFAULT '',
                avatar_url VARCHAR(255) DEFAULT '',
                profile TEXT DEFAULT '{}'
            )
            """
        )
    # 生成bcrypt哈希
    password_hash = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            INSERT INTO admin_users (
                email, username, password_hash, role,
                is_active, is_verified, created_at, updated_at
            ) VALUES (
                %s, %s, %s, 'super_admin',
                TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            RETURNING id
            """,
            (email, username, password_hash)
        )
        new_id = cursor.fetchone()["id"]
        conn.commit()
        return new_id


def main() -> None:
    """主流程：检查旧库→确保新库存在管理员"""
    load_env()

    # 新库配置（从 .env 读取）
    NEW_HOST = os.getenv('DB_HOST', 'pgm-2zekusmdjl0o3782ao.pg.rds.aliyuncs.com')
    PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'weplus_db')
    USER = os.getenv('DB_USER', 'weplus_db')
    PASSWORD = os.getenv('DB_PASSWORD', '123456yzlA')

    # 旧库配置（固定，仅用于调研是否已有管理员）
    OLD_HOST = 'pgm-2ze58b40mdfqec4zwo.pg.rds.aliyuncs.com'

    dsn_new = build_dsn(NEW_HOST, PORT, DB_NAME, USER, PASSWORD)
    dsn_old = build_dsn(OLD_HOST, PORT, DB_NAME, USER, PASSWORD)

    # 检查旧库管理员存在性
    try:
        with connect(dsn_old) as conn_old:
            old_has_admin = admin_exists(conn_old)
            print(f"旧库是否存在管理员 admin@weplus.com: {'是' if old_has_admin else '否'}")
    except Exception as e:
        print(f"旧库检查出错（忽略，不影响新库创建）：{e}")
        old_has_admin = False

    # 确保新库存在管理员
    try:
        with connect(dsn_new) as conn_new:
            if admin_exists(conn_new):
                print("✅ 新库已存在管理员 admin@weplus.com，跳过创建")
            else:
                new_id = create_admin(conn_new)
                print(f"✅ 已在新库创建管理员，ID={new_id}，账号=admin@weplus.com / admin123")
    except Exception as e:
        print(f"❌ 新库创建管理员失败：{e}")
        print("💡 请检查：1）admin_users 表是否已创建；2）账户是否有写权限；3）网络连通性；")

    print("\n完成：管理员账户保障流程")


if __name__ == "__main__":
    main()
