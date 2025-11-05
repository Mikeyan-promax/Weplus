# ChromaDB到PostgreSQL pgvector迁移分析报告

## 📊 当前架构分析

### 1. ChromaDB使用情况
- **存储位置**: `data/vector_store/chromadb/chroma.sqlite3`
- **向量维度**: 2560 (豆包嵌入模型doubao-embedding-text-240715)
- **集合名称**: `weplus_documents`
- **数据结构**:
  - 文档ID + 分块索引作为唯一标识
  - 每个分块包含：内容、嵌入向量、元数据
  - 支持时间戳和文档元数据

### 2. FAISS并行使用
- **索引类型**: IndexFlatIP (内积相似度)
- **存储文件**: `faiss_index.bin` + `faiss_id_map.json`
- **功能**: 提供快速向量搜索能力

### 3. PostgreSQL pgvector现状
✅ **已安装pgvector扩展** (`requirements.txt`中包含`pgvector==0.2.4`)
✅ **已有向量表结构**:
```sql
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- 注意：当前是1536维，需要调整为2560维
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

✅ **已有向量搜索函数**:
- `semantic_search()` - 语义搜索
- `hybrid_search()` - 混合搜索（语义+关键词）

✅ **已有向量索引**:
```sql
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
```

## 🔄 迁移策略

### 阶段1: 数据库架构调整
1. **向量维度调整**: 1536 → 2560
2. **表结构优化**: 确保与ChromaDB数据结构兼容
3. **索引重建**: 适配新的向量维度

### 阶段2: 数据迁移
1. **从ChromaDB导出数据**:
   - 文档分块内容
   - 2560维嵌入向量
   - 元数据和时间戳
2. **转换并导入PostgreSQL**:
   - 保持文档ID和分块索引关系
   - 转换向量格式
   - 迁移元数据

### 阶段3: 代码重构
1. **移除ChromaDB依赖**:
   - `vector_store_service.py`中的ChromaDB客户端
   - 相关import语句
2. **实现PostgreSQL向量操作**:
   - 向量存储
   - 相似度搜索
   - 批量操作
3. **保持API兼容性**: 确保现有RAG系统无缝切换

## 🎯 技术优势

### PostgreSQL pgvector vs ChromaDB
| 特性 | ChromaDB | PostgreSQL pgvector |
|------|----------|-------------------|
| 存储方式 | SQLite文件 | 原生PostgreSQL |
| 向量搜索 | 专用向量数据库 | SQL + 向量操作符 |
| 事务支持 | 有限 | 完整ACID |
| 扩展性 | 单机 | 分布式友好 |
| 云端部署 | 需要文件存储 | 标准数据库服务 |
| 查询能力 | 向量专用 | SQL + 向量混合 |

### 向量操作符对比
- **ChromaDB**: 内置相似度计算
- **pgvector**: 
  - `<=>` 余弦距离
  - `<->` L2距离  
  - `<#>` 内积距离

## 📋 迁移检查清单

### ✅ 已完成
- [x] pgvector扩展已安装
- [x] 基础表结构已存在
- [x] 向量搜索函数已实现
- [x] SQLite数据已备份

### 🔄 待完成
- [ ] 调整向量维度 (1536→2560)
- [ ] 迁移ChromaDB数据到PostgreSQL
- [ ] 重构vector_store_service.py
- [ ] 移除ChromaDB和FAISS依赖
- [ ] 更新requirements.txt
- [ ] 全面测试向量搜索功能

## 🚀 预期收益

1. **简化架构**: 单一数据库，减少复杂性
2. **提升性能**: 原生SQL查询 + 向量操作
3. **增强可靠性**: PostgreSQL的ACID特性
4. **便于部署**: 标准数据库服务，无需文件存储
5. **更好扩展**: 支持分布式和云端部署

## ⚠️ 风险评估

1. **向量维度不匹配**: 需要重新生成嵌入向量或调整模型
2. **性能差异**: 需要测试pgvector vs ChromaDB的搜索性能
3. **API兼容性**: 确保现有RAG系统功能不受影响

## 📈 下一步行动

1. 立即调整PostgreSQL表结构的向量维度
2. 实现数据迁移脚本
3. 重构向量存储服务
4. 进行全面测试和性能对比