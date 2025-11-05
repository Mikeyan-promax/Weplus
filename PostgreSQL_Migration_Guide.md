# PostgreSQL迁移指南

## 已自动转换的语法

### 1. 数据类型转换
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
- `TEXT` → `VARCHAR`
- `BLOB` → `BYTEA`
- `REAL` → `DOUBLE PRECISION`

### 2. 函数转换
- `datetime('now')` → `NOW()`
- `LENGTH()` → `CHAR_LENGTH()`
- `SUBSTR()` → `SUBSTRING()`
- `strftime()` → `TO_CHAR()`

### 3. PRAGMA语句处理
所有PRAGMA语句已被注释或转换为PostgreSQL等效语句。

### 4. 系统表转换
- `sqlite_master` → `information_schema.tables`

## 需要手动处理的语法

### 1. UPSERT操作
SQLite的 `INSERT OR REPLACE` 需要改为PostgreSQL的 `ON CONFLICT` 语法：

```sql
-- SQLite
INSERT OR REPLACE INTO table (id, name) VALUES (1, 'test');

-- PostgreSQL
INSERT INTO table (id, name) VALUES (1, 'test')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;
```

### 2. 事务处理
PostgreSQL的事务处理更严格，需要确保：
- 所有事务都有明确的BEGIN/COMMIT
- 错误处理包含ROLLBACK

### 3. 数据类型精度
某些数据类型可能需要指定精度：
- `VARCHAR` → `VARCHAR(255)`
- `DECIMAL` → `DECIMAL(10,2)`

## 连接池配置

使用新的PostgreSQL连接配置：

```python
from database.postgresql_config import get_db_connection, return_db_connection

# 获取连接
conn = get_db_connection()
try:
    # 执行操作
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
finally:
    # 归还连接
    return_db_connection(conn)
```

## 性能优化建议

1. 使用连接池避免频繁连接
2. 使用预编译语句防止SQL注入
3. 合理使用索引
4. 考虑使用JSONB替代TEXT存储JSON数据
