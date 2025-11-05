-- WePlus 生产化迁移：为日志相关表添加高频查询索引
-- 说明：本迁移脚本仅创建索引，表结构由应用启动自愈（LoggingService.ensure_log_tables）负责
-- 数据库：PostgreSQL

-- 系统日志表 system_logs 索引
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_category ON system_logs(category);
CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);

-- 用户操作日志表 user_action_logs 索引
CREATE INDEX IF NOT EXISTS idx_user_action_logs_user_id ON user_action_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_action_logs_action ON user_action_logs(action);
CREATE INDEX IF NOT EXISTS idx_user_action_logs_resource_type ON user_action_logs(resource_type);
CREATE INDEX IF NOT EXISTS idx_user_action_logs_created_at ON user_action_logs(created_at);

-- API访问日志表 api_access_logs 索引
CREATE INDEX IF NOT EXISTS idx_api_access_logs_method ON api_access_logs(method);
CREATE INDEX IF NOT EXISTS idx_api_access_logs_path ON api_access_logs(path);
CREATE INDEX IF NOT EXISTS idx_api_access_logs_status_code ON api_access_logs(status_code);
CREATE INDEX IF NOT EXISTS idx_api_access_logs_user_id ON api_access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_api_access_logs_created_at ON api_access_logs(created_at);

-- 提示：如需回滚，可按需 DROP INDEX IF EXISTS <index_name>;
