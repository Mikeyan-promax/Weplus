# WePlus 校园智能AI助手系统架构设计文档

## 📋 项目概述

**项目名称**: WePlus 校园智能AI助手  
**版本**: 2.0 (重构版)  
**开发时间**: 2025年1月  
**架构师**: Claude-4-Sonnet AI  

## 🎯 系统目标

1. **智能对话**: 基于DeepSeek的校园AI助手
2. **知识管理**: 完整的RAG知识库管理系统
3. **开发者后台**: 可视化的管理界面
4. **用户管理**: 完整的用户认证和管理系统

## 🏗️ 系统架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                    WePlus 系统架构                           │
├─────────────────────────────────────────────────────────────┤
│  前端层 (Frontend Layer)                                    │
│  ├── AI聊天界面 (React + TypeScript)                        │
│  ├── 开发者后台管理 (React Admin Dashboard)                  │
│  └── 知识库管理组件 (Knowledge Base Management)              │
├─────────────────────────────────────────────────────────────┤
│  API网关层 (API Gateway Layer)                              │
│  ├── 认证中间件 (Authentication Middleware)                 │
│  ├── 权限控制 (Authorization)                               │
│  └── 请求路由 (Request Routing)                             │
├─────────────────────────────────────────────────────────────┤
│  业务逻辑层 (Business Logic Layer)                          │
│  ├── AI对话服务 (Chat Service)                              │
│  ├── RAG检索服务 (RAG Retrieval Service)                    │
│  ├── 文档管理服务 (Document Management Service)              │
│  ├── 用户管理服务 (User Management Service)                 │
│  └── 知识库服务 (Knowledge Base Service)                    │
├─────────────────────────────────────────────────────────────┤
│  数据访问层 (Data Access Layer)                             │
│  ├── SQLite ORM (用户数据、文档元数据)                       │
│  ├── 向量数据库接口 (ChromaDB/FAISS)                        │
│  └── 文件存储接口 (Local File System)                       │
├─────────────────────────────────────────────────────────────┤
│  数据存储层 (Data Storage Layer)                            │
│  ├── SQLite数据库 (结构化数据)                               │
│  ├── ChromaDB (向量存储)                                    │
│  ├── FAISS (向量索引)                                       │
│  └── 本地文件系统 (文档存储)                                 │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 技术栈详细规划

### 前端技术栈
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI库**: Ant Design / Material-UI
- **状态管理**: Zustand / Redux Toolkit
- **路由**: React Router v6
- **HTTP客户端**: Axios
- **实时通信**: WebSocket / Server-Sent Events

### 后端技术栈
- **框架**: FastAPI (Python 3.9+)
- **异步处理**: asyncio + uvicorn
- **数据库ORM**: SQLAlchemy
- **认证**: JWT + OAuth2
- **文档处理**: PyPDF2, python-docx, BeautifulSoup
- **向量化**: sentence-transformers
- **AI集成**: DeepSeek API

### 数据存储技术栈
- **关系数据库**: SQLite (开发) / PostgreSQL (生产)
- **向量数据库**: ChromaDB + FAISS
- **缓存**: Redis (可选)
- **文件存储**: 本地文件系统 / 云存储

## 📊 数据库设计

### 1. 用户管理表结构

```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role ENUM('user', 'admin', 'developer') DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    profile_data JSON
);

-- 用户会话表
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);
```

### 2. 文档管理表结构

```sql
-- 文档表 (已存在，需要扩展)
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    upload_time TEXT DEFAULT CURRENT_TIMESTAMP,
    content_hash TEXT UNIQUE NOT NULL,
    doc_metadata TEXT DEFAULT '{}',
    status TEXT DEFAULT 'uploaded',
    -- 新增字段
    uploader_id INTEGER REFERENCES users(id),
    category_id INTEGER REFERENCES categories(id),
    tags JSON,
    is_public BOOLEAN DEFAULT FALSE,
    access_level ENUM('public', 'private', 'restricted') DEFAULT 'private',
    description TEXT,
    language VARCHAR(10) DEFAULT 'zh-CN'
);

-- 文档分类表
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES categories(id),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 文档标签表
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#1890ff',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文档标签关联表
CREATE TABLE document_tags (
    document_id INTEGER REFERENCES documents(id),
    tag_id INTEGER REFERENCES tags(id),
    PRIMARY KEY (document_id, tag_id)
);
```

### 3. 对话管理表结构

```sql
-- 对话会话表
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    session_metadata JSON
);

-- 对话消息表
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES chat_sessions(id),
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_metadata JSON,
    referenced_documents JSON -- 引用的文档ID列表
);
```

## 🔄 API设计规范

### 1. RESTful API 结构

```
/api/v1/
├── auth/                    # 认证相关
│   ├── POST /login         # 用户登录
│   ├── POST /register      # 用户注册
│   ├── POST /logout        # 用户登出
│   └── GET /profile        # 获取用户信息
├── users/                   # 用户管理
│   ├── GET /               # 获取用户列表
│   ├── GET /{id}           # 获取用户详情
│   ├── PUT /{id}           # 更新用户信息
│   └── DELETE /{id}        # 删除用户
├── documents/               # 文档管理
│   ├── GET /               # 获取文档列表
│   ├── POST /              # 上传文档
│   ├── GET /{id}           # 获取文档详情
│   ├── PUT /{id}           # 更新文档信息
│   ├── DELETE /{id}        # 删除文档
│   └── POST /{id}/process  # 处理文档
├── categories/              # 分类管理
│   ├── GET /               # 获取分类列表
│   ├── POST /              # 创建分类
│   ├── PUT /{id}           # 更新分类
│   └── DELETE /{id}        # 删除分类
├── tags/                    # 标签管理
│   ├── GET /               # 获取标签列表
│   ├── POST /              # 创建标签
│   └── DELETE /{id}        # 删除标签
├── chat/                    # 对话管理
│   ├── GET /sessions       # 获取对话会话
│   ├── POST /sessions      # 创建对话会话
│   ├── GET /sessions/{id}  # 获取会话详情
│   ├── POST /sessions/{id}/messages # 发送消息
│   └── DELETE /sessions/{id} # 删除会话
└── rag/                     # RAG相关
    ├── POST /search        # 语义搜索
    ├── POST /query         # RAG查询
    └── GET /stats          # 统计信息
```

### 2. WebSocket API

```
/ws/chat/{session_id}        # 实时对话
/ws/admin/monitor           # 系统监控
/ws/documents/process       # 文档处理状态
```

## 🎨 前端架构设计

### 1. 组件层次结构

```
src/
├── components/              # 通用组件
│   ├── Layout/             # 布局组件
│   ├── Chat/               # 聊天组件
│   ├── DocumentManager/    # 文档管理组件
│   ├── UserManager/        # 用户管理组件
│   └── Common/             # 通用UI组件
├── pages/                  # 页面组件
│   ├── ChatPage/           # AI聊天页面
│   ├── AdminDashboard/     # 管理后台
│   ├── KnowledgeBase/      # 知识库管理
│   └── UserProfile/        # 用户资料
├── hooks/                  # 自定义Hooks
├── services/               # API服务
├── stores/                 # 状态管理
├── utils/                  # 工具函数
└── types/                  # TypeScript类型定义
```

### 2. 状态管理设计

```typescript
// 全局状态结构
interface AppState {
  auth: {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
  };
  chat: {
    sessions: ChatSession[];
    currentSession: ChatSession | null;
    messages: Message[];
    isLoading: boolean;
  };
  documents: {
    list: Document[];
    categories: Category[];
    tags: Tag[];
    filters: DocumentFilters;
    pagination: Pagination;
  };
  ui: {
    theme: 'light' | 'dark';
    sidebarCollapsed: boolean;
    notifications: Notification[];
  };
}
```

## 🔐 安全设计

### 1. 认证与授权
- **JWT Token**: 用户认证
- **Role-Based Access Control (RBAC)**: 基于角色的权限控制
- **API Rate Limiting**: API调用频率限制
- **CORS配置**: 跨域请求安全

### 2. 数据安全
- **密码加密**: bcrypt哈希
- **敏感数据加密**: AES-256
- **SQL注入防护**: 参数化查询
- **XSS防护**: 输入验证和输出编码

## 📈 性能优化策略

### 1. 前端优化
- **代码分割**: 路由级别的懒加载
- **缓存策略**: HTTP缓存 + 浏览器缓存
- **虚拟滚动**: 大列表性能优化
- **防抖节流**: 搜索和输入优化

### 2. 后端优化
- **数据库索引**: 关键字段索引优化
- **连接池**: 数据库连接池管理
- **异步处理**: 文档处理异步化
- **缓存层**: Redis缓存热点数据

### 3. 向量检索优化
- **索引优化**: FAISS索引调优
- **批量处理**: 向量化批量操作
- **相似度阈值**: 动态调整检索阈值

## 🚀 部署架构

### 1. 开发环境
```
Docker Compose:
├── frontend (Vite Dev Server)
├── backend (FastAPI + uvicorn)
├── database (SQLite)
├── vector-db (ChromaDB)
└── redis (可选)
```

### 2. 生产环境
```
Kubernetes/Docker:
├── Frontend (Nginx + React Build)
├── Backend (Gunicorn + FastAPI)
├── Database (PostgreSQL)
├── Vector DB (ChromaDB Cluster)
├── Redis Cluster
└── Load Balancer
```

## 📋 开发里程碑

### Phase 1: 基础架构重构 (1-2周)
- [ ] 数据库结构重新设计
- [ ] 用户认证系统实现
- [ ] 基础API框架搭建
- [ ] 前端架构重构

### Phase 2: 核心功能开发 (2-3周)
- [ ] 文档管理系统完善
- [ ] RAG系统集成
- [ ] AI对话功能优化
- [ ] 知识库管理界面

### Phase 3: 高级功能 (2-3周)
- [ ] 开发者后台管理
- [ ] 高级搜索和过滤
- [ ] 批量操作功能
- [ ] 系统监控和日志

### Phase 4: 优化和部署 (1-2周)
- [ ] 性能优化
- [ ] 安全加固
- [ ] 部署自动化
- [ ] 文档完善

## 🔧 技术债务清理

### 当前问题修复
1. ✅ **删除功能持久化问题** - 已修复
2. **数据库架构混乱** - 需要重构
3. **API接口不统一** - 需要标准化
4. **前端状态管理混乱** - 需要重新设计
5. **错误处理不完善** - 需要统一处理

### 代码质量提升
- **TypeScript严格模式**: 启用严格类型检查
- **ESLint + Prettier**: 代码风格统一
- **单元测试**: 核心功能测试覆盖
- **API文档**: Swagger/OpenAPI文档
- **代码注释**: 关键逻辑注释完善

---

**文档版本**: v1.0  
**最后更新**: 2025-01-20  
**下一步**: 开始Phase 1基础架构重构