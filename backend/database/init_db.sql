-- RAG系统数据库初始化脚本
-- 创建数据库
CREATE DATABASE rag_system;

-- 连接到rag_system数据库
\c rag_system;

-- 启用pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建文档表
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'uploaded' -- uploaded, processing, processed, failed
);

-- 创建文档块表（用于存储分块后的文本和向量）
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content VARCHAR NOT NULL,
    content_length INTEGER NOT NULL,
    embedding VECTOR(1536), -- DeepSeek embedding维度为1536
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

-- 创建对话会话表
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) UNIQUE NOT NULL,
    user_id VARCHAR(100),
    title VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- 创建对话消息表
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL, -- user, assistant, system
    content VARCHAR NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建检索记录表（用于分析和优化）
CREATE TABLE retrieval_logs (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36),
    query VARCHAR NOT NULL,
    query_embedding VECTOR(1536),
    retrieved_chunks INTEGER[],
    similarity_scores FLOAT[],
    retrieval_method VARCHAR(50), -- semantic, keyword, hybrid
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引优化查询性能
-- 文档表索引
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_upload_time ON documents(upload_time);
CREATE INDEX idx_documents_file_type ON documents(file_type);

-- 文档块表索引
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_content_length ON document_chunks(content_length);

-- 向量相似度搜索索引（HNSW算法）
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- 对话相关索引
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_created_at ON chat_sessions(created_at);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);

-- 检索日志索引
CREATE INDEX idx_retrieval_logs_session_id ON retrieval_logs(session_id);
CREATE INDEX idx_retrieval_logs_created_at ON retrieval_logs(created_at);

-- 创建全文搜索索引（用于关键词检索）
CREATE INDEX idx_document_chunks_content_fts ON document_chunks USING gin(to_tsvector('english', content));

-- 创建视图：文档统计
CREATE VIEW document_stats AS
SELECT 
    d.id,
    d.filename,
    d.file_type,
    d.file_size,
    d.upload_time,
    d.status,
    COUNT(dc.id) as chunk_count,
    AVG(dc.content_length) as avg_chunk_length,
    SUM(dc.content_length) as total_content_length
FROM documents d
LEFT JOIN document_chunks dc ON d.id = dc.document_id
GROUP BY d.id, d.filename, d.file_type, d.file_size, d.upload_time, d.status;

-- 创建函数：相似度搜索
CREATE OR REPLACE FUNCTION search_similar_chunks(
    query_embedding VECTOR(1536),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE(
    chunk_id INTEGER,
    document_id INTEGER,
    filename VARCHAR(255),
    content VARCHAR,
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

-- 创建函数：混合检索（语义+关键词）
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text VARCHAR,
    query_embedding VECTOR(1536),
    semantic_weight FLOAT DEFAULT 0.7,
    keyword_weight FLOAT DEFAULT 0.3,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE(
    chunk_id INTEGER,
    document_id INTEGER,
    filename VARCHAR(255),
    content VARCHAR,
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

-- 插入初始数据
INSERT INTO chat_sessions (session_id, title) VALUES 
('default-session', '默认对话会话');

-- 创建数据库用户（可选）
-- CREATE USER rag_user WITH PASSWORD 'your_password';
-- GRANT ALL PRIVILEGES ON DATABASE rag_system TO rag_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rag_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rag_user;

COMMENT ON DATABASE rag_system IS 'RAG系统数据库 - 存储文档、向量嵌入和对话数据';
COMMENT ON TABLE documents IS '文档基本信息表';
COMMENT ON TABLE document_chunks IS '文档分块和向量存储表';
COMMENT ON TABLE chat_sessions IS '对话会话表';
COMMENT ON TABLE chat_messages IS '对话消息表';
COMMENT ON TABLE retrieval_logs IS '检索日志表，用于分析和优化';