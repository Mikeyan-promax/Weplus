<div align="center">

# WePlus - Campus Smart Assistant Platform

**Full-stack campus smart assistant powered by RAG · Monorepo · Single-container deployment**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-4169E1)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED)](https://www.docker.com/)
[![Railway](https://img.shields.io/badge/Railway-deploy-7C3AED)](https://railway.app/)

---

[📘 中文文档](README.md)

</div>

---

<p align="center">
  <a href="#introduction">Introduction</a> •
  <a href="#live-demo">Live Demo</a> •
  <a href="#whats-new">What's New</a> •
  <a href="#key-features">Key Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#deployment">Deployment</a> •
  <a href="#project-structure">Project Structure</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#api-reference">API Reference</a> •
  <a href="#roadmap">Roadmap</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## Introduction

**WePlus** is a full-stack campus smart assistant platform powered by **RAG (Retrieval-Augmented Generation)** technology. It integrates LLM capabilities with pgvector vector search to provide intelligent Q&A, document management, and learning resource sharing for campus users.

> 🎯 **Design Goal**: Build a production-ready full-stack web application showcasing modern web development best practices.
> <img width="3112" height="1937" alt="屏幕截图 2025-11-08 145751" src="https://github.com/user-attachments/assets/4e860a48-8972-4bc8-abb2-390418e269db" />
### Use Cases

| Scenario | Description |
|----------|-------------|
| 🎓 **Campus Q&A** | AI assistant powered by campus knowledge base |
| 📄 **Document Intelligence** | Upload PDF/Word/Excel for auto-parsing and semantic search |
| 📚 **Resource Sharing** | Upload, categorize, rate, and preview learning resources |
| 🔧 **Admin Console** | User management, system monitoring, audit logs, backup |


---

## Live Demo

<!--
  TODO: Replace with actual URLs after deployment.
  Example:
  - Frontend: https://weplus-demo.railway.app
  - API: https://weplus-demo.railway.app/api/healthz
-->

| Service | URL |
|---------|------|
| 🌐 Frontend | Available after deployment |
| 📡 API Health | Available after deployment |
| 📖 Swagger Docs | Available after deployment |

> 💡 You can also run the project locally by following the [Quick Start](#quick-start) guide.

### Screenshots

> The following pages are available when the project is running:

| Page | Description |
|------|-------------|
| 🤖 RAG Chat | Chat with AI based on uploaded documents |
| 📚 Study Resources | Browse, upload, and search learning materials |
| 👤 User Center | Register, login, and manage profile |
| 🛠️ Admin Panel | Dashboard, user management, audit logs |

> <img width="3023" height="1839" alt="屏幕截图 2025-11-08 145914" src="https://github.com/user-attachments/assets/f2fd4d5c-0c36-4aa6-9011-3e5577f513a2" />
---

## What's New

### 🚀 Recent Updates

| Date | Update |
|------|--------|
| 2026-Q1 | Migrated database from SQLite to PostgreSQL + pgvector |
| 2026-Q1 | Migrated vector store from ChromaDB + FAISS to pgvector |
| 2026-Q1 | Refactored Docker deployment to single-container (Nginx + Supervisord + Uvicorn) |
| 2026-Q1 | Added Railway cloud deployment support |
| 2026-Q1 | Restructured project documentation into organized docs |
| 2026-Q1 | Integrated Sentry error tracking and Prometheus monitoring |
| 2025-Q4 | Completed RAG engine core functionality |
| 2025-Q4 | Completed front-end/back-end separation architecture |

### ⭐ Stay Tuned

If you find this project helpful, feel free to Star it to receive notifications on future updates!

---

## Key Features

### 🤖 RAG-Powered Chat

- **Documents as Knowledge Base**: Upload PDF, Word, Excel, PPT to build your knowledge base
- **Semantic Search**: pgvector-based vector similarity search for accurate retrieval
- **Streaming Response**: Server-Sent Events for real-time typewriter effect
- **Multi-turn Dialogue**: Context-aware conversation with memory
<img width="1919" height="1034" alt="image" src="https://github.com/user-attachments/assets/26d40e26-76f5-4201-a64d-163148b43c1d" />

### 📚 Learning Resource Management

- **Multi-format Support**: Documents, images, videos
- **Tag & Category**: Flexible classification system
- **Community Features**: Rating, comments, favorites
- **Online Preview**: View documents without downloading
<img width="3025" height="1903" alt="屏幕截图 2025-11-08 145953" src="https://github.com/user-attachments/assets/eff42d14-522b-4f2b-84b8-f840e9a931de" />
### 👥 User System

- **JWT Authentication**: Token-based auth with auto-refresh
- **Email Verification**: Prevent bot registrations
- **Role-based Access**: User / Admin two-tier permissions
- **Security**: bcrypt hashing, rate limiting, IP whitelist
<img width="1510" height="870" alt="image" src="https://github.com/user-attachments/assets/bd43cdbc-2992-43de-8a89-bcbccc16e684" />
### 🛠️ Admin Dashboard

- **System Overview**: Real-time statistics and charts
- **User Management**: CRUD, status management, permissions
- **Document Management**: Upload records, storage stats
- **Vector Database**: Index rebuild, cleanup optimization
- **Audit Logs**: Operation audit, log query and export
- **Backup & Restore**: One-click backup and recovery

### 🔧 Testing & Monitoring

- **Health Check**: `/api/healthz` endpoint for component status
- **API Testing**: Comprehensive endpoint test suite
- **Performance**: Prometheus metrics collection
- **Error Tracking**: Sentry integration
- **Structured Logging**: JSON format for log analysis

---

## Architecture

### Overview

```
┌─────────────────────────────────────────────────────────┐
│                    User Layer                            │
│         Web Browser · Mobile · API Clients              │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────┐
│                   Gateway Layer                          │
│    Nginx (Reverse Proxy · Static Files · SSL)            │
│    CORS · Rate Limiting · Request ID                     │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                Application Layer                         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Auth        │  │ RAG Engine   │  │ Resource Mgmt  │ │
│  │ JWT·bcrypt  │  │ Retrieve·Gen │  │ CRUD·Search    │ │
│  ├─────────────┤  ├──────────────┤  ├────────────────┤ │
│  │ Admin       │  │ Doc Processor│  │ Monitoring     │ │
│  │ Dashboard   │  │ Parse·Chunk  │  │ Metrics·Logs   │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
│                   FastAPI + Uvicorn                      │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                    Data Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ PostgreSQL   │  │ pgvector     │  │ File Storage   │ │
│  │ Relational   │  │ Vector Data  │  │ Uploads        │ │
│  └──────────────┘  └──────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | FastAPI + Uvicorn | High-performance async web framework |
| **ORM** | SQLAlchemy 2.0 | Database ORM |
| **Database** | PostgreSQL 14+ + pgvector | Relational + Vector storage |
| **AI** | DeepSeek API + Doubao Embedding | LLM + Embeddings |
| **Documents** | PyPDF2 · python-docx · openpyxl · python-pptx | Multi-format parsing |
| **Auth** | JWT · bcrypt · HTTPBearer | Authentication & security |
| **Frontend** | React 19 + TypeScript + Vite 7 | Modern frontend |
| **Routing** | React Router DOM 7 | Client-side routing |
| **UI** | Framer Motion + Lucide React | Animations & icons |
| **Deploy** | Docker + Nginx + Supervisord | Single-container deploy |
| **Monitoring** | Sentry + Prometheus | Error tracking + metrics |

### RAG Query Flow

```
User Question
    │
    ▼
┌──────────────┐
│ Query        │ ← Intent recognition, keyword extraction
│ Understanding│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Vector       │ ← Text → Embedding → pgvector similarity search
│ Retrieval    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Context      │ ← Retrieved chunks + Question = Prompt
│ Fusion       │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ LLM          │ ← DeepSeek API → Streaming output
│ Generation   │
└──────┬───────┘
       │
       ▼
   Response (SSE Stream)
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (with pgvector extension)
- Docker 20.10+ (optional)

### 1. Clone

```bash
git clone https://github.com/Mikeyan-promax/WePlus_rebulid.git
cd weplus-12.0
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# ⚠️ Edit .env with your database URL and API keys

# Initialize database
python init_db.py

# Start dev server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend2

npm install

npm run dev
```

### 4. Access

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

---

## Deployment

### 🐳 Docker (Recommended)

```bash
# Docker Compose for production
docker-compose -f deploy/docker-compose.yml up -d

# Or build single-container image
docker build -t weplus:latest .
docker run -p 80:80 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e SECRET_KEY=your-secret-key \
  weplus:latest
```

### ☁️ Railway

One-click deploy to Railway with auto-build.

**Required Environment Variables:**

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key |
| `ALLOWED_ORIGINS` | CORS allowed origins |
| `OPENAI_API_KEY` | OpenAI / DeepSeek API key |

> 📖 See [Deployment Guide](docs/部署指南.md) for details.
<img width="3044" height="1920" alt="railway部署界面" src="https://github.com/user-attachments/assets/67903cba-cc8d-4839-871b-23056f4c25a6" />
---

## Project Structure

```
weplus-12.0/
├── backend/                        # FastAPI backend
│   ├── app/                       # Application core
│   │   ├── api/                  # API routes
│   │   ├── core/                 # Configuration
│   │   ├── dependencies/         # Security deps
│   │   ├── middlewares/          # Middleware
│   │   ├── models/               # Data models
│   │   └── services/             # Business logic
│   ├── database/                 # DB config & migrations
│   ├── scripts/                  # Utility scripts
│   ├── requirements.txt          # Python deps
│   └── main.py                   # Entry point
├── frontend2/                      # React frontend
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── contexts/             # React Context
│   │   ├── services/             # API clients
│   │   ├── types/                # TypeScript types
│   │   └── utils/                # Utilities
│   ├── public/                   # Static assets
│   └── package.json              # Frontend deps
├── deploy/                        # Deployment configs
│   ├── nginx.conf                # Nginx configuration
│   ├── docker-compose.yml        # Docker Compose
│   └── checks/                   # Deployment checks
├── docs/                          # Documentation
│   ├── 项目架构设计文档.md
│   ├── 部署指南.md
│   ├── 数据库迁移与配置指南.md
│   ├── 开发过程记录_完整版.md
│   ├── 后台管理系统开发记录.md
│   └── 系统测试与问题分析报告.md
├── scripts/                       # Automation scripts
├── Dockerfile                     # Single-container Dockerfile
├── railway.json                   # Railway configuration
└── README.md                      # Chinese documentation
```

---

## Documentation

In addition to this README, the project provides detailed documentation in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [📐 Architecture Design](docs/项目架构设计文档.md) | System architecture, design decisions, security |
| [🚀 Deployment Guide](docs/部署指南.md) | Local dev, Docker, Railway, operations |
| [🗄️ Database Migration Guide](docs/数据库迁移与配置指南.md) | SQLite→PostgreSQL, ChromaDB→pgvector, RDS |
| [📝 Development Log](docs/开发过程记录_完整版.md) | Complete development history, changelog |
| [📊 Admin System Dev Log](docs/后台管理系统开发记录.md) | Admin panel features and implementation |
| [🧪 Testing & Analysis Report](docs/系统测试与问题分析报告.md) | Test reports, issue analysis, architecture review |

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register with email verification |
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/auth/send-verification-code` | Send email code |

### RAG Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/rag/chat` | Chat message (SSE stream) |
| POST | `/api/rag/documents/upload` | Upload document |
| GET | `/api/rag/documents` | List documents |
| DELETE | `/api/rag/documents/{id}` | Delete document |
| GET | `/api/rag/health` | Health check |

### Study Resources

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/study-resources` | List resources |
| POST | `/api/study-resources/upload` | Upload resource |
| GET | `/api/study-resources/{id}/download` | Download |
| POST | `/api/study-resources/{id}/rate` | Rate resource |
| POST | `/api/study-resources/{id}/comment` | Add comment |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/dashboard` | Dashboard stats |
| GET | `/api/admin/users` | User list |
| GET | `/api/admin/logs` | System logs |
| POST | `/api/admin/backup` | Create backup |

> 📋 See [WePlus_API接口清单.md](WePlus_API接口清单.md) for the complete API reference.

---

## Roadmap

### 🎯 Completed

- [x] User registration / login / JWT authentication
- [x] RAG engine: document upload, vector retrieval, LLM generation
- [x] Study resources CRUD + search + rating & comments
- [x] Admin dashboard: overview, user management, logs
- [x] PostgreSQL + pgvector database migration
- [x] Docker single-container + Railway cloud deployment
- [x] Sentry error tracking + Prometheus monitoring

### 🗺️ Planned

- [ ] Mobile responsive optimization
- [ ] OAuth third-party login (WeChat, GitHub)
- [ ] WebSocket real-time notifications
- [ ] Internationalization (i18n)
- [ ] Knowledge base visualization graph
- [ ] Batch document import & auto-classification
- [ ] CI/CD automated pipeline
- [ ] Unit test coverage > 80%

---

## Contributing

### Workflow

1. **Fork** the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit: `git commit -m "feat: add amazing feature"`
4. Push: `git push origin feature/amazing-feature`
5. Open a **Pull Request**

### Commit Convention

| Type | Description |
|------|-------------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation |
| `style:` | Code style |
| `refactor:` | Refactoring |
| `test:` | Testing |
| `chore:` | Build/tooling |

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

### Community

| Channel | Description |
|---------|-------------|
| 🐛 [Issues](https://github.com/Mikeyan-promax/WePlus_rebulid/issues) | Report bugs or suggest features |
| 💬 [Discussions](https://github.com/Mikeyan-promax/WePlus_rebulid/discussions) | Join technical discussions |
| 🔀 [Pull Requests](https://github.com/Mikeyan-promax/WePlus_rebulid/pulls) | Submit code contributions |

---

## License

[MIT](LICENSE) © WePlus Contributors

---

<p align="center">
  <b>WePlus - Making Campus Smarter</b><br>
  <sub>Built with ❤️ for the campus community</sub>
  <br><br>
  <a href="#introduction">⬆ Back to Top</a> ｜ <a href="README.md">📘 中文文档</a>
</p>
