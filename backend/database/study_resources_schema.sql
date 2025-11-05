-- 学习资源系统数据库表结构
-- 创建时间: 2024-12-25

-- 1. 资源分类表 (resource_categories)
CREATE TABLE IF NOT EXISTS resource_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,           -- 分类名称：英语四六级、雅思、考研等
    code VARCHAR(50) NOT NULL UNIQUE,            -- 分类代码：cet, ielts, postgraduate等
    description TEXT DEFAULT '',                  -- 分类描述
    icon VARCHAR(50) DEFAULT '',                 -- 分类图标
    color VARCHAR(20) DEFAULT '#4A90E2',         -- 分类主题色
    sort_order INTEGER DEFAULT 0,               -- 排序顺序
    is_active BOOLEAN DEFAULT TRUE,                -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 学习资源表 (study_resources)
CREATE TABLE IF NOT EXISTS study_resources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,                  -- 资源名称
    description TEXT DEFAULT '',                 -- 资源描述
    file_name VARCHAR(255) NOT NULL,             -- 文件名
    file_path VARCHAR(500) NOT NULL,             -- 文件存储路径
    file_type VARCHAR(20) NOT NULL,              -- 文件类型：PDF, DOCX, MP3, MP4等
    file_size BIGINT NOT NULL,                   -- 文件大小（字节）
    category_id INTEGER NOT NULL,               -- 分类ID
    
    -- 统计信息
    download_count INTEGER DEFAULT 0,           -- 下载次数
    view_count INTEGER DEFAULT 0,               -- 查看次数
    rating_avg DECIMAL(3,2) DEFAULT 0.00,       -- 平均评分
    rating_count INTEGER DEFAULT 0,             -- 评分人数
    
    -- 状态和时间
    status VARCHAR(20) DEFAULT 'active',        -- 状态：active, inactive, deleted
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 元数据
    metadata TEXT DEFAULT '{}',                  -- JSON格式的额外信息
    tags TEXT DEFAULT '[]',                      -- JSON数组格式的标签
    keywords TEXT DEFAULT '[]',                  -- JSON数组格式的关键词
    
    -- 外键约束
    FOREIGN KEY (category_id) REFERENCES resource_categories (id) ON DELETE RESTRICT
);

-- 3. 资源评分表 (resource_ratings)
CREATE TABLE IF NOT EXISTS resource_ratings (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER NOT NULL,               -- 资源ID
    user_id VARCHAR(100) NOT NULL,              -- 用户ID（来自用户系统）
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5), -- 评分1-5星
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 确保每个用户对每个资源只能评分一次
    UNIQUE(resource_id, user_id),
    FOREIGN KEY (resource_id) REFERENCES study_resources (id) ON DELETE CASCADE
);

-- 4. 资源评论表 (resource_comments)
CREATE TABLE IF NOT EXISTS resource_comments (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER NOT NULL,               -- 资源ID
    user_id VARCHAR(100) NOT NULL,              -- 用户ID
    user_name VARCHAR(100) DEFAULT '',          -- 用户昵称（冗余存储）
    content VARCHAR NOT NULL,                      -- 评论内容
    parent_id INTEGER DEFAULT NULL,             -- 父评论ID（支持回复）
    
    -- 状态
    status VARCHAR(20) DEFAULT 'active',        -- 状态：active, hidden, deleted
    is_pinned BOOLEAN DEFAULT FALSE,                -- 是否置顶
    
    -- 时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (resource_id) REFERENCES study_resources (id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES resource_comments (id) ON DELETE CASCADE
);

-- 5. 资源下载记录表 (resource_downloads)
CREATE TABLE IF NOT EXISTS resource_downloads (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER NOT NULL,               -- 资源ID
    user_id VARCHAR(100) DEFAULT NULL,          -- 用户ID（可为空，支持匿名下载）
    ip_address VARCHAR(45) DEFAULT '',          -- IP地址
    user_agent TEXT DEFAULT '',                 -- 用户代理
    download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 下载状态
    status VARCHAR(20) DEFAULT 'completed',     -- 状态：started, completed, failed
    file_size BIGINT DEFAULT 0,                 -- 下载的文件大小
    
    FOREIGN KEY (resource_id) REFERENCES study_resources (id) ON DELETE CASCADE
);

-- 6. 资源标签表 (resource_tags)
CREATE TABLE IF NOT EXISTS resource_tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,           -- 标签名称
    description TEXT DEFAULT '',                -- 标签描述
    color VARCHAR(20) DEFAULT '#6c757d',        -- 标签颜色
    usage_count INTEGER DEFAULT 0,             -- 使用次数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 资源标签关联表 (resource_tag_relations)
CREATE TABLE IF NOT EXISTS resource_tag_relations (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER NOT NULL,              -- 资源ID
    tag_id INTEGER NOT NULL,                   -- 标签ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 确保同一资源不会重复关联同一标签
    UNIQUE(resource_id, tag_id),
    FOREIGN KEY (resource_id) REFERENCES study_resources (id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES resource_tags (id) ON DELETE CASCADE
);

-- 8. 资源收藏表 (resource_favorites)
CREATE TABLE IF NOT EXISTS resource_favorites (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER NOT NULL,              -- 资源ID
    user_id VARCHAR(100) NOT NULL,             -- 用户ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 确保每个用户对每个资源只能收藏一次
    UNIQUE(resource_id, user_id),
    FOREIGN KEY (resource_id) REFERENCES study_resources (id) ON DELETE CASCADE
);

-- 创建索引以提高查询性能

-- 资源分类表索引
CREATE INDEX IF NOT EXISTS idx_resource_categories_code ON resource_categories(code);
CREATE INDEX IF NOT EXISTS idx_resource_categories_active ON resource_categories(is_active);

-- 学习资源表索引
CREATE INDEX IF NOT EXISTS idx_study_resources_category ON study_resources(category_id);
CREATE INDEX IF NOT EXISTS idx_study_resources_status ON study_resources(status);
CREATE INDEX IF NOT EXISTS idx_study_resources_upload_time ON study_resources(upload_time);
CREATE INDEX IF NOT EXISTS idx_study_resources_rating ON study_resources(rating_avg);
CREATE INDEX IF NOT EXISTS idx_study_resources_downloads ON study_resources(download_count);
CREATE INDEX IF NOT EXISTS idx_study_resources_file_type ON study_resources(file_type);

-- 全文搜索索引（SQLite FTS5）
CREATE VIRTUAL TABLE IF NOT EXISTS study_resources_fts USING fts5(
    name, description, keywords, content='study_resources', content_rowid='id'
);

-- 评分表索引
CREATE INDEX IF NOT EXISTS idx_resource_ratings_resource ON resource_ratings(resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_ratings_user ON resource_ratings(user_id);

-- 评论表索引
CREATE INDEX IF NOT EXISTS idx_resource_comments_resource ON resource_comments(resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_comments_user ON resource_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_resource_comments_parent ON resource_comments(parent_id);
CREATE INDEX IF NOT EXISTS idx_resource_comments_status ON resource_comments(status);

-- 下载记录表索引
CREATE INDEX IF NOT EXISTS idx_resource_downloads_resource ON resource_downloads(resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_downloads_user ON resource_downloads(user_id);
CREATE INDEX IF NOT EXISTS idx_resource_downloads_time ON resource_downloads(download_time);

-- 标签关联表索引
CREATE INDEX IF NOT EXISTS idx_resource_tag_relations_resource ON resource_tag_relations(resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_tag_relations_tag ON resource_tag_relations(tag_id);

-- 收藏表索引
CREATE INDEX IF NOT EXISTS idx_resource_favorites_resource ON resource_favorites(resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_favorites_user ON resource_favorites(user_id);

-- 插入初始分类数据
INSERT INTO ... ON CONFLICT DO NOTHING resource_categories (name, code, description, icon, color, sort_order) VALUES
('英语四六级', 'cet', '英语四六级考试相关资料，包括真题、词汇、听力、写作等备考资源', '🎓', '#4A90E2', 1),
('雅思备考', 'ielts', '雅思考试备考资料，涵盖听说读写四个模块的学习资源', '🌍', '#7ED321', 2),
('考研资料', 'postgraduate', '研究生入学考试资料，包括政治、英语、数学、专业课等复习资源', '📚', '#F5A623', 3),
('专业课程', 'professional', '各专业核心课程学习资料，实验指导，课件PPT等教学资源', '🔬', '#BD10E0', 4),
('软件技能', 'software', '编程语言、开发工具、软件应用等技能学习教程和资料', '💻', '#50E3C2', 5),
('学术写作', 'academic', '学术论文写作指导，研究方法，学术规范等相关资源', '✍️', '#FF6B6B', 6);

-- 插入一些示例标签
INSERT INTO ... ON CONFLICT DO NOTHING resource_tags (name, description, color) VALUES
('真题', '历年考试真题', '#dc3545'),
('模拟题', '模拟练习题目', '#fd7e14'),
('词汇', '词汇学习资料', '#20c997'),
('听力', '听力训练资料', '#6f42c1'),
('写作', '写作指导资料', '#0dcaf0'),
('语法', '语法学习资料', '#198754'),
('高频', '高频考点资料', '#ffc107'),
('基础', '基础入门资料', '#6c757d'),
('进阶', '进阶提高资料', '#0d6efd'),
('冲刺', '考前冲刺资料', '#d63384');

-- 创建触发器：自动更新资源评分统计
CREATE TRIGGER IF NOT EXISTS update_resource_rating_stats
AFTER INSERT ON resource_ratings
BEGIN
    UPDATE study_resources 
    SET 
        rating_avg = (
            SELECT ROUND(AVG(CAST(rating AS DOUBLE PRECISION PRECISION)), 2) 
            FROM resource_ratings 
            WHERE resource_id = NEW.resource_id
        ),
        rating_count = (
            SELECT COUNT(*) 
            FROM resource_ratings 
            WHERE resource_id = NEW.resource_id
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.resource_id;
END;

-- 创建触发器：自动更新下载统计
CREATE TRIGGER IF NOT EXISTS update_download_count
AFTER INSERT ON resource_downloads
WHEN NEW.status = 'completed'
BEGIN
    UPDATE study_resources 
    SET 
        download_count = download_count + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.resource_id;
END;

-- 创建触发器：自动更新标签使用统计
CREATE TRIGGER IF NOT EXISTS update_tag_usage_count
AFTER INSERT ON resource_tag_relations
BEGIN
    UPDATE resource_tags 
    SET usage_count = usage_count + 1
    WHERE id = NEW.tag_id;
END;

-- 创建视图：资源详细信息
CREATE VIEW IF NOT EXISTS resource_details AS
SELECT 
    r.id,
    r.name,
    r.description,
    r.file_name,
    r.file_type,
    r.file_size,
    r.download_count,
    r.view_count,
    r.rating_avg,
    r.rating_count,
    r.upload_time,
    r.status,
    c.name as category_name,
    c.code as category_code,
    c.color as category_color,
    c.icon as category_icon
FROM study_resources r
LEFT JOIN resource_categories c ON r.category_id = c.id
WHERE r.status = 'active' AND c.is_active = 1;

-- 创建视图：分类统计
CREATE VIEW IF NOT EXISTS category_stats AS
SELECT 
    c.id,
    c.name,
    c.code,
    c.description,
    c.icon,
    c.color,
    COUNT(r.id) as resource_count,
    COALESCE(SUM(r.download_count), 0) as total_downloads,
    COALESCE(AVG(r.rating_avg), 0) as avg_rating
FROM resource_categories c
LEFT JOIN study_resources r ON c.id = r.category_id AND r.status = 'active'
WHERE c.is_active = 1
GROUP BY c.id, c.name, c.code, c.description, c.icon, c.color
ORDER BY c.sort_order;

-- PostgreSQL foreign keys are always enabled;