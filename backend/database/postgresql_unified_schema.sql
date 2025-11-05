-- WePlus 统一PostgreSQL数据库架构 (完全迁移版本)
-- 移除所有SQLite依赖，统一使用PostgreSQL
-- 支持2560维向量 (豆包嵌入模型)
-- 创建时间: 2024-10-30

-- 连接到数据库
-- \c weplus_db;

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- 用于文本相似度搜索

-- ========================================
-- 用户认证系统
-- ========================================

-- 1. 用户表 (替代users.db)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) DEFAULT '',
    avatar_url VARCHAR(500) DEFAULT '',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- 2. 用户会话表
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- ========================================
-- RAG系统相关表
-- ========================================

-- 3. 文档表
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    uploader_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'uploaded' -- uploaded, processing, processed, failed
);

-- 4. 文档块表（用于存储分块后的文本和向量）
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_length INTEGER NOT NULL,
    embedding VECTOR(2560), -- 调整为2560维 (豆包嵌入模型)
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

-- 5. 对话会话表
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- 6. 对话消息表
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 检索记录表（用于分析和优化）
CREATE TABLE IF NOT EXISTS retrieval_logs (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36),
    query TEXT NOT NULL,
    query_embedding VECTOR(2560), -- 调整为2560维
    retrieved_chunks INTEGER[],
    similarity_scores FLOAT[],
    retrieval_method VARCHAR(50), -- semantic, keyword, hybrid
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- 学习资源系统相关表 (替代study_resources.db)
-- ========================================

-- 8. 资源分类表
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

-- 9. 学习资源表
CREATE TABLE IF NOT EXISTS study_resources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_size BIGINT NOT NULL,
    category_id INTEGER REFERENCES resource_categories(id) ON DELETE SET NULL,
    uploader_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    download_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- ========================================
-- 管理后台系统 (替代admin.db, weplus_admin.db)
-- ========================================

-- 10. 管理员用户表
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    real_name VARCHAR(100) DEFAULT '',
    role VARCHAR(20) DEFAULT 'admin', -- super_admin, admin, moderator
    permissions JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. 系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL, -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    message TEXT NOT NULL,
    module VARCHAR(100) DEFAULT '',
    function_name VARCHAR(100) DEFAULT '',
    line_number INTEGER,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    admin_id INTEGER REFERENCES admin_users(id) ON DELETE SET NULL,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- 12. 用户操作日志表
CREATE TABLE IF NOT EXISTS user_action_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. 文件记录表
CREATE TABLE IF NOT EXISTS file_records (
    id SERIAL PRIMARY KEY,
    original_name VARCHAR(255) NOT NULL,
    stored_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    uploader_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_processed BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB DEFAULT '{}'
);

-- 14. 知识库条目表 (替代knowledge_base.db)
CREATE TABLE IF NOT EXISTS knowledge_entries (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    source_file_id INTEGER REFERENCES file_records(id) ON DELETE SET NULL,
    category VARCHAR(100) DEFAULT '',
    summary TEXT DEFAULT '',
    keywords TEXT[] DEFAULT '{}',
    importance_score DOUBLE PRECISION DEFAULT 0.0,
    access_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    embedding_model VARCHAR(100) DEFAULT 'doubao-embedding-text-240715',
    vector_dimension INTEGER DEFAULT 2560,
    similarity_threshold DOUBLE PRECISION DEFAULT 0.7,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- 15. 系统统计表
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
    total_chat_sessions INTEGER DEFAULT 0,
    total_chat_messages INTEGER DEFAULT 0,
    vector_search_count INTEGER DEFAULT 0,
    avg_response_time DOUBLE PRECISION DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- 向量搜索函数 (支持2560维)
-- ========================================

-- 语义搜索函数
CREATE OR REPLACE FUNCTION semantic_search(
    query_embedding VECTOR(2560),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE(
    chunk_id INTEGER,
    document_id INTEGER,
    filename VARCHAR(255),
    content TEXT,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dc.id as chunk_id,
        dc.document_id,
        d.filename,
        dc.content,
        1 - (dc.embedding <=> query_embedding) as similarity_score
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE d.status = 'processed'
    AND 1 - (dc.embedding <=> query_embedding) > similarity_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- 混合检索函数（语义+关键词）
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text TEXT,
    query_embedding VECTOR(2560),
    semantic_weight FLOAT DEFAULT 0.7,
    keyword_weight FLOAT DEFAULT 0.3,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE(
    chunk_id INTEGER,
    document_id INTEGER,
    filename VARCHAR(255),
    content TEXT,
    combined_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dc.id as chunk_id,
        dc.document_id,
        d.filename,
        dc.content,
        (semantic_weight * (1 - (dc.embedding <=> query_embedding)) + 
         keyword_weight * ts_rank(to_tsvector('english', dc.content), plainto_tsquery('english', query_text))) as combined_score
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE d.status = 'processed'
    AND (
        1 - (dc.embedding <=> query_embedding) > 0.5
        OR to_tsvector('english', dc.content) @@ plainto_tsquery('english', query_text)
    )
    ORDER BY combined_score DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 索引创建
-- ========================================

-- 向量索引 (HNSW算法，支持2560维)
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- 全文搜索索引
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_fts 
ON document_chunks USING gin(to_tsvector('english', content));

-- 用户相关索引
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);

-- 文档相关索引
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);

-- 会话相关索引
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);

-- 学习资源索引
CREATE INDEX IF NOT EXISTS idx_study_resources_category_id ON study_resources(category_id);
CREATE INDEX IF NOT EXISTS idx_study_resources_uploader_id ON study_resources(uploader_id);

-- 日志索引
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_user_action_logs_user_id ON user_action_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_action_logs_created_at ON user_action_logs(created_at);

-- ========================================
-- 触发器函数
-- ========================================

-- 更新时间戳触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON chat_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_resource_categories_updated_at BEFORE UPDATE ON resource_categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_study_resources_updated_at BEFORE UPDATE ON study_resources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_admin_users_updated_at BEFORE UPDATE ON admin_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_knowledge_entries_updated_at BEFORE UPDATE ON knowledge_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_stats_updated_at BEFORE UPDATE ON system_stats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- 初始数据插入
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

-- 插入默认聊天会话
INSERT INTO chat_sessions (session_id, title) VALUES 
('default-session', '默认对话会话')
ON CONFLICT (session_id) DO NOTHING;

-- ========================================
-- 数据库权限设置 (可选)
-- ========================================

-- 创建数据库用户（如果需要）
-- CREATE USER weplus_user WITH PASSWORD 'your_secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE weplus_db TO weplus_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO weplus_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO weplus_user;