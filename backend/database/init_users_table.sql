-- 创建用户表的SQL脚本
-- 用于登录注册系统的用户数据存储

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

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_is_verified ON users(is_verified);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为用户表创建更新时间触发器
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 添加邮箱格式检查约束
ALTER TABLE users 
ADD CONSTRAINT check_email_format 
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- 添加用户名长度检查约束
ALTER TABLE users 
ADD CONSTRAINT check_username_length 
CHECK (CHAR_LENGTH(username) >= 2 AND CHAR_LENGTH(username) <= 50);

-- 插入测试数据（可选，用于开发测试）
-- INSERT INTO users (email, username, password_hash, is_verified) 
-- VALUES ('test@example.com', 'testuser', '$2b$12$example_hash', true)
-- ON CONFLICT (email) DO NOTHING;

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