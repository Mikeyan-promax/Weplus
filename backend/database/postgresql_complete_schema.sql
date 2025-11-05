-- WePlus 完整数据库初始化脚本 (PostgreSQL版本)
-- 包含RAG系统、学习资源系统和后台管理系统的所有表结构
-- 创建时间: 2024-12-25

-- 连接到数据库
-- \c weplus_db;

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ========================================
-- RAG系统相关表
-- ========================================

-- 1. 文档表
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'uploaded' -- uploaded, processing, processed, failed
);

-- 2. 文档块表（用于存储分块后的文本和向量）
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_length INTEGER NOT NULL,
    embedding VECTOR(1536), -- DeepSeek embedding维度为1536
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

-- 3. 对话会话表
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) UNIQUE NOT NULL,
    user_id VARCHAR(100),
    title VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- 4. 对话消息表
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 检索记录表（用于分析和优化）
CREATE TABLE IF NOT EXISTS retrieval_logs (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36),
    query TEXT NOT NULL,
    query_embedding VECTOR(1536),
    retrieved_chunks INTEGER[],
    similarity_scores FLOAT[],
    retrieval_method VARCHAR(50), -- semantic, keyword, hybrid
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- 学习资源系统相关表
-- ========================================

-- 6. 资源分类表
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
);

-- 7. 学习资源表
CREATE TABLE IF NOT EXISTS study_resources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_size BIGINT NOT NULL,
    category_id INTEGER NOT NULL,
    
    -- 统计信息
    download_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    rating_avg DECIMAL(3,2) DEFAULT 0.00,
    rating_count INTEGER DEFAULT 0,
    
    -- 状态和时间
    status VARCHAR(20) DEFAULT 'active',
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 元数据
    metadata TEXT DEFAULT '{}',
    tags TEXT DEFAULT '[]',
    keywords TEXT DEFAULT '[]',
    
    FOREIGN KEY (category_id) REFERENCES resource_categories (id) ON DELETE RESTRICT
);

-- 8. 资源评分表
CREATE TABLE IF NOT EXISTS resource_ratings (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(resource_id, user_id),
    FOREIGN KEY (resource_id) REFERENCES study_resources (id) ON DELETE CASCADE
);

-- 9. 资源评论表
CREATE TABLE IF NOT EXISTS resource_comments (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    user_name VARCHAR(100) DEFAULT '',
    content TEXT NOT NULL,
    parent_id INTEGER DEFAULT NULL,
    
    status VARCHAR(20) DEFAULT 'active',
    is_pinned BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (resource_id) REFERENCES study_resources (id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES resource_comments (id) ON DELETE CASCADE
);

-- 10. 资源下载记录表
CREATE TABLE IF NOT EXISTS resource_downloads (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER NOT NULL,
    user_id VARCHAR(100) DEFAULT NULL,
    ip_address VARCHAR(45) DEFAULT '',
    user_agent TEXT DEFAULT '',
    download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    status VARCHAR(20) DEFAULT 'completed',
    file_size BIGINT DEFAULT 0,
    
    FOREIGN KEY (resource_id) REFERENCES study_resources (id) ON DELETE CASCADE
);

-- ========================================
-- 后台管理系统相关表
-- ========================================

-- 11. 管理员用户表
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
    profile TEXT DEFAULT '{}'
);

-- 12. 文件记录表
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
    file_hash VARCHAR(32) DEFAULT '',
    download_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT FALSE,
    category VARCHAR(100) DEFAULT '',
    description TEXT DEFAULT '',
    
    -- 处理相关字段
    extracted_text TEXT DEFAULT '',
    processing_error TEXT DEFAULT '',
    processed_at TIMESTAMP,
    
    -- JSON字段存储标签
    tags TEXT DEFAULT '[]',
    
    FOREIGN KEY (user_id) REFERENCES admin_users (id) ON DELETE SET NULL
);

-- 13. RAG知识库条目表
CREATE TABLE IF NOT EXISTS knowledge_entries (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    source_file_id INTEGER,
    vector_id VARCHAR(100) DEFAULT '',
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
    keywords TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}',
    
    FOREIGN KEY (source_file_id) REFERENCES file_records (id) ON DELETE SET NULL
);

-- 14. 系统统计表
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

-- 15. 用户会话表
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

-- 16. 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    operation_type VARCHAR(50) NOT NULL,
    operation_detail TEXT DEFAULT '',
    target_resource VARCHAR(100) DEFAULT '',
    target_id INTEGER DEFAULT NULL,
    ip_address INET,
    user_agent TEXT DEFAULT '',
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES admin_users (id) ON DELETE SET NULL
);

-- ========================================
-- 创建索引优化查询性能
-- ========================================

-- RAG系统索引
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_upload_time ON documents(upload_time);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_length ON document_chunks(content_length);

-- 向量相似度搜索索引（HNSW算法）
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);

CREATE INDEX IF NOT EXISTS idx_retrieval_logs_session_id ON retrieval_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_logs_created_at ON retrieval_logs(created_at);

-- 全文搜索索引
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_fts ON document_chunks USING gin(to_tsvector('english', content));

-- 学习资源系统索引
CREATE INDEX IF NOT EXISTS idx_resource_categories_code ON resource_categories(code);
CREATE INDEX IF NOT EXISTS idx_resource_categories_is_active ON resource_categories(is_active);

CREATE INDEX IF NOT EXISTS idx_study_resources_category_id ON study_resources(category_id);
CREATE INDEX IF NOT EXISTS idx_study_resources_status ON study_resources(status);
CREATE INDEX IF NOT EXISTS idx_study_resources_upload_time ON study_resources(upload_time);
CREATE INDEX IF NOT EXISTS idx_study_resources_file_type ON study_resources(file_type);

CREATE INDEX IF NOT EXISTS idx_resource_ratings_resource_id ON resource_ratings(resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_ratings_user_id ON resource_ratings(user_id);

CREATE INDEX IF NOT EXISTS idx_resource_comments_resource_id ON resource_comments(resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_comments_user_id ON resource_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_resource_comments_parent_id ON resource_comments(parent_id);

CREATE INDEX IF NOT EXISTS idx_resource_downloads_resource_id ON resource_downloads(resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_downloads_user_id ON resource_downloads(user_id);
CREATE INDEX IF NOT EXISTS idx_resource_downloads_download_time ON resource_downloads(download_time);

-- 后台管理系统索引
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);
CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role);
CREATE INDEX IF NOT EXISTS idx_admin_users_is_active ON admin_users(is_active);

CREATE INDEX IF NOT EXISTS idx_file_records_user_id ON file_records(user_id);
CREATE INDEX IF NOT EXISTS idx_file_records_file_type ON file_records(file_type);
CREATE INDEX IF NOT EXISTS idx_file_records_processing_status ON file_records(processing_status);
CREATE INDEX IF NOT EXISTS idx_file_records_upload_time ON file_records(upload_time);

CREATE INDEX IF NOT EXISTS idx_knowledge_entries_source_file_id ON knowledge_entries(source_file_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_entries_category ON knowledge_entries(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_entries_is_active ON knowledge_entries(is_active);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_operation_logs_user_id ON operation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_operation_type ON operation_logs(operation_type);
CREATE INDEX IF NOT EXISTS idx_operation_logs_created_at ON operation_logs(created_at);

-- ========================================
-- 创建触发器和函数
-- ========================================

-- 自动更新updated_at字段的函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加触发器
CREATE TRIGGER update_resource_categories_updated_at BEFORE UPDATE ON resource_categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_study_resources_updated_at BEFORE UPDATE ON study_resources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_resource_ratings_updated_at BEFORE UPDATE ON resource_ratings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_resource_comments_updated_at BEFORE UPDATE ON resource_comments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_admin_users_updated_at BEFORE UPDATE ON admin_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_knowledge_entries_updated_at BEFORE UPDATE ON knowledge_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_stats_updated_at BEFORE UPDATE ON system_stats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON chat_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- 插入初始数据
-- ========================================

-- 插入默认的超级管理员用户
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

-- ========================================
-- 添加表注释
-- ========================================

COMMENT ON TABLE documents IS 'RAG系统文档表';
COMMENT ON TABLE document_chunks IS 'RAG系统文档块表，存储分块后的文本和向量';
COMMENT ON TABLE chat_sessions IS 'RAG系统对话会话表';
COMMENT ON TABLE chat_messages IS 'RAG系统对话消息表';
COMMENT ON TABLE retrieval_logs IS 'RAG系统检索记录表';

COMMENT ON TABLE resource_categories IS '学习资源分类表';
COMMENT ON TABLE study_resources IS '学习资源表';
COMMENT ON TABLE resource_ratings IS '资源评分表';
COMMENT ON TABLE resource_comments IS '资源评论表';
COMMENT ON TABLE resource_downloads IS '资源下载记录表';

COMMENT ON TABLE admin_users IS '后台管理用户表';
COMMENT ON TABLE file_records IS '文件记录表';
COMMENT ON TABLE knowledge_entries IS 'RAG知识库条目表';
COMMENT ON TABLE system_stats IS '系统统计表';
COMMENT ON TABLE user_sessions IS '用户会话表';
COMMENT ON TABLE operation_logs IS '操作日志表';