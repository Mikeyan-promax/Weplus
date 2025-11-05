#!/usr/bin/env python3
"""
PostgreSQL数据库初始化脚本
"""

import psycopg2
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_db_connection():
    """获取数据库连接"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

def init_database():
    """初始化数据库表"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("开始初始化PostgreSQL数据库...")
        
        # 1. 创建资源分类表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resource_categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                code VARCHAR(50) NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                icon VARCHAR(50) DEFAULT '',
                color VARCHAR(20) DEFAULT '#4A90E2',
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ 资源分类表创建成功")
        
        # 2. 创建学习资源表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_resources (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT DEFAULT '',
                file_name VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_type VARCHAR(20) NOT NULL,
                file_size BIGINT NOT NULL,
                category_id INTEGER NOT NULL,
                download_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                rating_avg DECIMAL(3,2) DEFAULT 0.00,
                rating_count INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'active',
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                tags TEXT DEFAULT '[]',
                keywords TEXT DEFAULT '[]',
                FOREIGN KEY (category_id) REFERENCES resource_categories (id) ON DELETE RESTRICT
            )
        """)
        print("✅ 学习资源表创建成功")
        
        # 3. 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_study_resources_category ON study_resources(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_study_resources_status ON study_resources(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_study_resources_created_at ON study_resources(created_at)")
        print("✅ 索引创建成功")
        
        # 4. 插入默认分类数据
        cursor.execute("""
            INSERT INTO resource_categories (name, code, description, icon, color, sort_order) VALUES
            ('英语四六级', 'cet', '大学英语四六级考试资料，包括真题、模拟题、词汇、听力等学习资源', '📚', '#4A90E2', 1),
            ('雅思备考', 'ielts', '雅思考试备考资料，涵盖听说读写四个模块的学习资源', '🌍', '#7ED321', 2),
            ('考研资料', 'postgraduate', '研究生入学考试资料，包括政治、英语、数学、专业课等复习资源', '📖', '#F5A623', 3),
            ('专业课程', 'professional', '各专业核心课程学习资料，实验指导，课件PPT等教学资源', '🔬', '#BD10E0', 4),
            ('软件技能', 'software', '编程语言、开发工具、软件应用等技能学习教程和资料', '💻', '#50E3C2', 5),
            ('学术写作', 'academic', '学术论文写作指导，研究方法，学术规范等相关资源', '✍️', '#FF6B6B', 6)
            ON CONFLICT (code) DO NOTHING
        """)
        print("✅ 默认分类数据插入成功")
        
        # 5. 创建管理员用户表
        cursor.execute("""
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
        """)
        print("✅ 管理员用户表创建成功")
        
        # 6. 插入默认管理员账户
        cursor.execute("""
            INSERT INTO admin_users (email, username, password_hash, role, is_active, is_verified) VALUES
            ('admin@weplus.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJY9.k5W6', 'super_admin', TRUE, TRUE)
            ON CONFLICT (email) DO NOTHING
        """)
        print("✅ 默认管理员账户创建成功")
        
        conn.commit()
        print("🎉 PostgreSQL数据库初始化完成！")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    init_database()