-- WePlus 后台管理系统数据库初始化脚本
-- 创建用户管理、文件管理和RAG知识库管理所需的所有表

-- 1. 用户表 (admin_users)
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin', 'super_admin')),
    is_active BOOLEAN DEFAULT 1,
    is_verified BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    login_count INTEGER DEFAULT 0,
    
    -- 扩展用户信息
    real_name VARCHAR(100) DEFAULT '',
    phone VARCHAR(20) DEFAULT '',
    department VARCHAR(100) DEFAULT '',
    student_id VARCHAR(50) DEFAULT '',
    avatar_url VARCHAR(255) DEFAULT '',
    
    -- JSON字段存储额外配置
    profile VARCHAR DEFAULT '{}' -- JSON格式的用户配置
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
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    content_summary VARCHAR DEFAULT '',
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed', 'vectorized')),
    user_id INTEGER,
    
    -- 新增字段
    file_hash VARCHAR(32) DEFAULT '', -- MD5哈希值
    download_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT 0,
    category VARCHAR(100) DEFAULT '',
    description VARCHAR DEFAULT '',
    
    -- 处理相关字段
    extracted_text VARCHAR DEFAULT '',
    processing_error VARCHAR DEFAULT '',
    processed_at DATETIME,
    
    -- JSON字段存储标签
    tags VARCHAR DEFAULT '[]', -- JSON数组格式的标签
    
    FOREIGN KEY (user_id) REFERENCES admin_users (id) ON DELETE SET NULL
);

-- 3. RAG知识库条目表 (knowledge_entries)
CREATE TABLE IF NOT EXISTS knowledge_entries (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content VARCHAR NOT NULL,
    source_file_id INTEGER,
    vector_id VARCHAR(100) DEFAULT '', -- 向量存储中的ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR(100) DEFAULT '',
    
    -- 新增字段
    summary VARCHAR DEFAULT '',
    importance_score DOUBLE PRECISION DEFAULT 0.0,
    access_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    
    -- 向量化相关
    embedding_model VARCHAR(100) DEFAULT '',
    vector_dimension INTEGER DEFAULT 0,
    similarity_threshold DOUBLE PRECISION DEFAULT 0.7,
    
    -- JSON字段
    keywords VARCHAR DEFAULT '[]', -- JSON数组格式的关键词
    metadata VARCHAR DEFAULT '{}', -- JSON格式的元数据
    
    FOREIGN KEY (source_file_id) REFERENCES file_records (id) ON DELETE SET NULL
);

-- 4. 系统统计表 (system_stats)
CREATE TABLE IF NOT EXISTS system_stats (
    id SERIAL PRIMARY KEY,
    stat_date DATE DEFAULT (CURRENT_DATE),
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    total_files INTEGER DEFAULT 0,
    total_file_size INTEGER DEFAULT 0,
    total_knowledge_entries INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0,
    pending_files INTEGER DEFAULT 0,
    failed_files INTEGER DEFAULT 0,
    
    -- 时间统计
    today_uploads INTEGER DEFAULT 0,
    this_week_uploads INTEGER DEFAULT 0,
    this_month_uploads INTEGER DEFAULT 0,
    
    -- JSON字段存储详细统计
    file_type_stats VARCHAR DEFAULT '{}', -- 按文件类型统计
    category_stats VARCHAR DEFAULT '{}',  -- 按分类统计
    
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stat_date) -- 每天一条记录
);

-- 5. 管理员操作日志表 (admin_logs)
CREATE TABLE IF NOT EXISTS admin_logs (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER,
    action VARCHAR(100) NOT NULL, -- 操作类型：login, logout, create_user, delete_file等
    target_type VARCHAR(50), -- 操作对象类型：user, file, knowledge_entry等
    target_id INTEGER, -- 操作对象ID
    description VARCHAR, -- 操作描述
    ip_address VARCHAR(45), -- IP地址
    user_agent VARCHAR, -- 用户代理
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- JSON字段存储额外信息
    extra_data VARCHAR DEFAULT '{}',
    
    FOREIGN KEY (admin_id) REFERENCES admin_users (id) ON DELETE SET NULL
);

-- 6. 文件分类表 (file_categories)
CREATE TABLE IF NOT EXISTS file_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description VARCHAR DEFAULT '',
    parent_id INTEGER, -- 支持分类层级
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_id) REFERENCES file_categories (id) ON DELETE SET NULL
);

-- 7. 向量存储元数据表 (vector_metadata)
CREATE TABLE IF NOT EXISTS vector_metadata (
    id SERIAL PRIMARY KEY,
    vector_id VARCHAR(100) UNIQUE NOT NULL,
    knowledge_entry_id INTEGER,
    embedding_model VARCHAR(100) NOT NULL,
    vector_dimension INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 向量相关信息
    chunk_index INTEGER DEFAULT 0, -- 文档分块索引
    chunk_size INTEGER DEFAULT 0,  -- 分块大小
    
    FOREIGN KEY (knowledge_entry_id) REFERENCES knowledge_entries (id) ON DELETE CASCADE
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);
CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role);
CREATE INDEX IF NOT EXISTS idx_admin_users_is_active ON admin_users(is_active);

CREATE INDEX IF NOT EXISTS idx_file_records_user_id ON file_records(user_id);
CREATE INDEX IF NOT EXISTS idx_file_records_file_type ON file_records(file_type);
CREATE INDEX IF NOT EXISTS idx_file_records_processing_status ON file_records(processing_status);
CREATE INDEX IF NOT EXISTS idx_file_records_upload_time ON file_records(upload_time);
CREATE INDEX IF NOT EXISTS idx_file_records_category ON file_records(category);
CREATE INDEX IF NOT EXISTS idx_file_records_file_hash ON file_records(file_hash);

CREATE INDEX IF NOT EXISTS idx_knowledge_entries_source_file_id ON knowledge_entries(source_file_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_entries_category ON knowledge_entries(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_entries_is_active ON knowledge_entries(is_active);
CREATE INDEX IF NOT EXISTS idx_knowledge_entries_created_at ON knowledge_entries(created_at);

CREATE INDEX IF NOT EXISTS idx_admin_logs_admin_id ON admin_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_action ON admin_logs(action);
CREATE INDEX IF NOT EXISTS idx_admin_logs_created_at ON admin_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_vector_metadata_vector_id ON vector_metadata(vector_id);
CREATE INDEX IF NOT EXISTS idx_vector_metadata_knowledge_entry_id ON vector_metadata(knowledge_entry_id);

-- 插入默认数据

-- 1. 插入默认管理员用户
INSERT INTO ... ON CONFLICT DO NOTHING admin_users (
    email, username, password_hash, role, real_name, is_active, is_verified
) VALUES (
    'admin@weplus.com', 
    'admin', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlG.', -- 密码: admin123
    'super_admin',
    '系统管理员',
    1,
    1
);

-- 2. 插入默认文件分类
INSERT INTO ... ON CONFLICT DO NOTHING file_categories (name, description, sort_order) VALUES
('学术文档', '学术论文、研究报告等', 1),
('课程资料', '课件、教材、作业等', 2),
('管理文件', '规章制度、通知公告等', 3),
('图片资源', '图片、图表、截图等', 4),
('其他文件', '其他类型文件', 99);

-- 3. 插入初始统计数据
INSERT INTO ... ON CONFLICT DO NOTHING system_stats (stat_date) VALUES (CURRENT_DATE);

-- 创建触发器自动更新时间戳
CREATE TRIGGER IF NOT EXISTS update_admin_users_timestamp 
    AFTER UPDATE ON admin_users
BEGIN
    UPDATE admin_users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_knowledge_entries_timestamp 
    AFTER UPDATE ON knowledge_entries
BEGIN
    UPDATE knowledge_entries SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 创建视图简化查询

-- 用户统计视图
CREATE VIEW IF NOT EXISTS v_user_stats AS
SELECT 
    COUNT(*) as total_users,
    COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_users,
    COUNT(CASE WHEN role = 'admin' THEN 1 END) as admin_users,
    COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) as today_registrations
FROM admin_users;

-- 文件统计视图
CREATE VIEW IF NOT EXISTS v_file_stats AS
SELECT 
    COUNT(*) as total_files,
    SUM(file_size) as total_size,
    COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as processed_files,
    COUNT(CASE WHEN processing_status = 'pending' THEN 1 END) as pending_files,
    COUNT(CASE WHEN processing_status = 'failed' THEN 1 END) as failed_files,
    COUNT(CASE WHEN DATE(upload_time) = CURRENT_DATE THEN 1 END) as today_uploads
FROM file_records;

-- 知识库统计视图
CREATE VIEW IF NOT EXISTS v_knowledge_stats AS
SELECT 
    COUNT(*) as total_entries,
    COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_entries,
    AVG(importance_score) as avg_importance,
    SUM(access_count) as total_access_count
FROM knowledge_entries;