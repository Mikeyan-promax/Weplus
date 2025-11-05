-- 创建用户学习记录表
CREATE TABLE IF NOT EXISTS user_study_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,                    -- 用户ID
    resource_id INTEGER NOT NULL,               -- 资源ID
    study_status VARCHAR(20) DEFAULT 'not_started', -- 学习状态：not_started, in_progress, paused, completed
    progress_percentage DECIMAL(5,2) DEFAULT 0.00, -- 学习进度百分比
    current_position VARCHAR(100) DEFAULT '',   -- 当前学习位置（页码、时间点等）
    total_study_time INTEGER DEFAULT 0,         -- 总学习时间（秒）
    started_at TIMESTAMP DEFAULT NULL,          -- 开始学习时间
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 最后访问时间
    completed_at TIMESTAMP DEFAULT NULL,        -- 完成时间
    notes TEXT DEFAULT '',                       -- 学习笔记
    rating INTEGER DEFAULT NULL CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5)), -- 评分
    review TEXT DEFAULT '',                      -- 评价
    access_count INTEGER DEFAULT 0,             -- 访问次数
    bookmark_count INTEGER DEFAULT 0,           -- 书签数量
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 确保每个用户对每个资源只有一条学习记录
    UNIQUE(user_id, resource_id),
    FOREIGN KEY (resource_id) REFERENCES study_resources (id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_study_records_user_id ON user_study_records(user_id);
CREATE INDEX IF NOT EXISTS idx_user_study_records_resource_id ON user_study_records(resource_id);
CREATE INDEX IF NOT EXISTS idx_user_study_records_status ON user_study_records(study_status);
CREATE INDEX IF NOT EXISTS idx_user_study_records_last_accessed ON user_study_records(last_accessed_at);

-- 创建触发器：自动更新updated_at字段
CREATE OR REPLACE FUNCTION update_user_study_records_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_study_records_updated_at_trigger
    BEFORE UPDATE ON user_study_records
    FOR EACH ROW
    EXECUTE FUNCTION update_user_study_records_updated_at();