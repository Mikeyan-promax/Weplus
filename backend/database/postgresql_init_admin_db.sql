-- WePlus 后台管理系统数据库初始化脚本 (PostgreSQL版本)
-- 创建用户管理、文件管理和RAG知识库管理所需的所有表

-- 1. 用户表 (admin_users)
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
    
    -- 扩展用户信息
    real_name VARCHAR(100) DEFAULT '',
    phone VARCHAR(20) DEFAULT '',
    department VARCHAR(100) DEFAULT '',
    student_id VARCHAR(50) DEFAULT '',
    avatar_url VARCHAR(255) DEFAULT '',
    
    -- JSON字段存储额外配置
    profile TEXT DEFAULT '{}' -- JSON格式的用户配置
);

-- 2. 文件记录表 (file_records)
CREATE TABLE IF NOT EXISTS file_records (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('pdf', 'doc', 'docx', 'txt', 'jpg', 'png', 'jpeg', 'other')),
    mime_type VARCHAR(100) DEFAULT '',
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_summary TEXT DEFAULT '',
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed', 'vectorized')),
    user_id INTEGER,
    
    -- 新增字段
    file_hash VARCHAR(32) DEFAULT '', -- MD5哈希值
    download_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT FALSE,
    category VARCHAR(100) DEFAULT '',
    description TEXT DEFAULT '',
    
    -- 处理相关字段
    extracted_text TEXT DEFAULT '',
    processing_error TEXT DEFAULT '',
    processed_at TIMESTAMP,
    
    -- JSON字段存储标签
    tags TEXT DEFAULT '[]', -- JSON数组格式的标签
    
    FOREIGN KEY (user_id) REFERENCES admin_users (id) ON DELETE SET NULL
);

-- 3. RAG知识库条目表 (knowledge_entries)
CREATE TABLE IF NOT EXISTS knowledge_entries (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    source_file_id INTEGER,
    vector_id VARCHAR(100) DEFAULT '', -- 向量存储中的ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR(100) DEFAULT '',
    
    -- 新增字段
    summary TEXT DEFAULT '',
    importance_score DOUBLE PRECISION DEFAULT 0.0,
    access_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 向量化相关
    embedding_model VARCHAR(100) DEFAULT '',
    vector_dimension INTEGER DEFAULT 0,
    similarity_threshold DOUBLE PRECISION DEFAULT 0.7,
    
    -- JSON字段
    keywords TEXT DEFAULT '[]', -- JSON数组格式的关键词
    metadata TEXT DEFAULT '{}', -- JSON格式的元数据
    
    FOREIGN KEY (source_file_id) REFERENCES file_records (id) ON DELETE SET NULL
);

-- 4. 系统统计表 (system_stats)
CREATE TABLE IF NOT EXISTS system_stats (
    id SERIAL PRIMARY KEY,
    stat_date DATE DEFAULT CURRENT_DATE,
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    total_files INTEGER DEFAULT 0,
    total_file_size BIGINT DEFAULT 0,
    total_knowledge_entries INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0,
    pending_files INTEGER DEFAULT 0,
    failed_files INTEGER DEFAULT 0,
    
    -- 系统性能统计
    avg_processing_time DOUBLE PRECISION DEFAULT 0.0,
    total_queries INTEGER DEFAULT 0,
    successful_queries INTEGER DEFAULT 0,
    
    -- 存储统计
    storage_used BIGINT DEFAULT 0,
    vector_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 用户会话表 (user_sessions)
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT DEFAULT '',
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (user_id) REFERENCES admin_users (id) ON DELETE CASCADE
);

-- 6. 操作日志表 (operation_logs)
CREATE TABLE IF NOT EXISTS operation_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    operation_type VARCHAR(50) NOT NULL, -- login, logout, upload, delete, query等
    operation_detail TEXT DEFAULT '',
    target_resource VARCHAR(100) DEFAULT '', -- 操作的资源类型
    target_id INTEGER DEFAULT NULL, -- 操作的资源ID
    ip_address INET,
    user_agent TEXT DEFAULT '',
    status VARCHAR(20) DEFAULT 'success', -- success, failed, pending
    error_message TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES admin_users (id) ON DELETE SET NULL
);

-- 创建索引优化查询性能
-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);
CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role);
CREATE INDEX IF NOT EXISTS idx_admin_users_is_active ON admin_users(is_active);
CREATE INDEX IF NOT EXISTS idx_admin_users_created_at ON admin_users(created_at);

-- 文件记录表索引
CREATE INDEX IF NOT EXISTS idx_file_records_user_id ON file_records(user_id);
CREATE INDEX IF NOT EXISTS idx_file_records_file_type ON file_records(file_type);
CREATE INDEX IF NOT EXISTS idx_file_records_processing_status ON file_records(processing_status);
CREATE INDEX IF NOT EXISTS idx_file_records_upload_time ON file_records(upload_time);
CREATE INDEX IF NOT EXISTS idx_file_records_file_hash ON file_records(file_hash);

-- 知识库条目表索引
CREATE INDEX IF NOT EXISTS idx_knowledge_entries_source_file_id ON knowledge_entries(source_file_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_entries_category ON knowledge_entries(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_entries_is_active ON knowledge_entries(is_active);
CREATE INDEX IF NOT EXISTS idx_knowledge_entries_created_at ON knowledge_entries(created_at);

-- 系统统计表索引
CREATE INDEX IF NOT EXISTS idx_system_stats_stat_date ON system_stats(stat_date);

-- 用户会话表索引
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);

-- 操作日志表索引
CREATE INDEX IF NOT EXISTS idx_operation_logs_user_id ON operation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_operation_type ON operation_logs(operation_type);
CREATE INDEX IF NOT EXISTS idx_operation_logs_created_at ON operation_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_operation_logs_status ON operation_logs(status);

-- 创建触发器自动更新updated_at字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加触发器
CREATE TRIGGER update_admin_users_updated_at BEFORE UPDATE ON admin_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_knowledge_entries_updated_at BEFORE UPDATE ON knowledge_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_stats_updated_at BEFORE UPDATE ON system_stats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入默认的超级管理员用户（密码需要在应用层进行哈希处理）
INSERT INTO admin_users (email, username, password_hash, role, is_active, is_verified, real_name) 
VALUES ('admin@weplus.com', 'admin', '$2b$12$placeholder_hash', 'super_admin', TRUE, TRUE, '系统管理员')
ON CONFLICT (email) DO NOTHING;

-- 插入默认的资源分类
INSERT INTO resource_categories (name, code, description, icon, color, sort_order) VALUES
('英语四六级', 'cet', '大学英语四六级考试资源', 'book', '#4A90E2', 1),
('雅思托福', 'ielts_toefl', '雅思和托福考试资源', 'globe', '#50C878', 2),
('考研资料', 'postgraduate', '研究生入学考试资源', 'graduation-cap', '#FF6B6B', 3),
('编程学习', 'programming', '编程和技术学习资源', 'code', '#9B59B6', 4),
('其他资源', 'others', '其他学习资源', 'folder', '#95A5A6', 99)
ON CONFLICT (code) DO NOTHING;

COMMENT ON TABLE admin_users IS '后台管理用户表';
COMMENT ON TABLE file_records IS '文件记录表';
COMMENT ON TABLE knowledge_entries IS 'RAG知识库条目表';
COMMENT ON TABLE system_stats IS '系统统计表';
COMMENT ON TABLE user_sessions IS '用户会话表';
COMMENT ON TABLE operation_logs IS '操作日志表';