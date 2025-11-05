"""
数据库初始化脚本
用于创建用户表和相关的索引、约束、触发器
"""

import asyncio
import asyncpg
import os
from config import DatabaseConfig

# 用户表创建SQL
CREATE_USERS_TABLE_SQL = """
-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    profile JSONB DEFAULT '{}'::jsonb
);
"""

# 创建索引SQL
CREATE_INDEXES_SQL = """
-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_is_verified ON users(is_verified);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
"""

# 创建触发器函数SQL
CREATE_TRIGGER_FUNCTION_SQL = """
-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
"""

# 创建触发器SQL
CREATE_TRIGGER_SQL = """
-- 为用户表创建更新时间触发器
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""

# 添加约束SQL
ADD_CONSTRAINTS_SQL = """
-- 添加邮箱格式检查约束
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'check_email_format' 
        AND table_name = 'users'
    ) THEN
        ALTER TABLE users 
        ADD CONSTRAINT check_email_format 
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$');
    END IF;
END $$;

-- 添加用户名长度检查约束
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'check_username_length' 
        AND table_name = 'users'
    ) THEN
        ALTER TABLE users 
        ADD CONSTRAINT check_username_length 
        CHECK (CHAR_LENGTH(username) >= 2 AND CHAR_LENGTH(username) <= 50);
    END IF;
END $$;
"""

# 添加注释SQL
ADD_COMMENTS_SQL = """
COMMENT ON TABLE users IS '用户表，存储登录注册系统的用户信息';
COMMENT ON COLUMN users.id IS '用户唯一标识符';
COMMENT ON COLUMN users.email IS '用户邮箱地址，用于登录和验证';
COMMENT ON COLUMN users.username IS '用户名，用于显示';
COMMENT ON COLUMN users.password_hash IS '密码哈希值，使用bcrypt加密';
COMMENT ON COLUMN users.is_active IS '用户是否激活状态';
COMMENT ON COLUMN users.is_verified IS '邮箱是否已验证';
COMMENT ON COLUMN users.created_at IS '用户创建时间';
COMMENT ON COLUMN users.updated_at IS '用户信息最后更新时间';
COMMENT ON COLUMN users.last_login IS '用户最后登录时间';
COMMENT ON COLUMN users.profile IS '用户扩展信息，JSON格式存储';
"""

async def init_database():
    """初始化数据库表结构"""
    db_config = DatabaseConfig()
    pool = None
    
    try:
        # 创建连接池
        pool = await db_config.create_pool()
        print("✅ 数据库连接成功")
        
        async with pool.acquire() as conn:
            # 执行SQL语句
            print("📝 创建用户表...")
            await conn.execute(CREATE_USERS_TABLE_SQL)
            print("✅ 用户表创建成功")
            
            print("📝 创建索引...")
            await conn.execute(CREATE_INDEXES_SQL)
            print("✅ 索引创建成功")
            
            print("📝 创建触发器函数...")
            await conn.execute(CREATE_TRIGGER_FUNCTION_SQL)
            print("✅ 触发器函数创建成功")
            
            print("📝 创建触发器...")
            await conn.execute(CREATE_TRIGGER_SQL)
            print("✅ 触发器创建成功")
            
            print("📝 添加约束...")
            await conn.execute(ADD_CONSTRAINTS_SQL)
            print("✅ 约束添加成功")
            
            print("📝 添加注释...")
            await conn.execute(ADD_COMMENTS_SQL)
            print("✅ 注释添加成功")
            
            # 验证表是否创建成功
            result = await conn.fetchrow("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = 'users' AND table_schema = 'public'
            """)
            
            if result:
                print("🎉 用户表初始化完成！")
                
                # 显示表结构
                columns = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                
                print("\n📋 用户表结构:")
                print("-" * 60)
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    print(f"{col['column_name']:<15} {col['data_type']:<20} {nullable}{default}")
                print("-" * 60)
            else:
                print("❌ 用户表创建失败")
                
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        print("💡 请确保PostgreSQL服务正在运行，并且数据库配置正确")
        print("💡 检查.env文件中的数据库连接信息")
        return False
    finally:
        if pool:
            await pool.close()
            print("🔒 数据库连接已关闭")
    
    return True

if __name__ == "__main__":
    print("🚀 开始初始化数据库...")
    asyncio.run(init_database())