"""
文档管理API模块
提供文档管理相关的API接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/documents", tags=["文档管理"])

# 数据模型
class Document(BaseModel):
    id: int
    title: str
    filename: str
    size: int
    type: str
    status: str
    created_at: str
    updated_at: str

class DocumentStats(BaseModel):
    total_documents: int
    active_documents: int
    pending_documents: int
    total_size: int

class DocumentResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str = ""

# 模拟数据
MOCK_DOCUMENTS = [
    {
        "id": 1,
        "title": "系统使用手册",
        "filename": "system_manual.pdf",
        "size": 2048576,
        "type": "pdf",
        "status": "active",
        "created_at": "2024-01-01 10:00:00",
        "updated_at": "2024-01-01 10:00:00"
    },
    {
        "id": 2,
        "title": "API文档",
        "filename": "api_docs.md",
        "size": 512000,
        "type": "markdown",
        "status": "active",
        "created_at": "2024-01-05 14:20:00",
        "updated_at": "2024-01-10 16:30:00"
    },
    {
        "id": 3,
        "title": "用户指南",
        "filename": "user_guide.docx",
        "size": 1024000,
        "type": "docx",
        "status": "pending",
        "created_at": "2024-01-10 16:45:00",
        "updated_at": "2024-01-10 16:45:00"
    }
]

@router.get("/", response_model=DocumentResponse)
async def get_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None)
):
    """获取文档列表"""
    try:
        # 模拟数据过滤
        filtered_docs = MOCK_DOCUMENTS.copy()
        
        if search:
            filtered_docs = [
                doc for doc in filtered_docs
                if search.lower() in doc["title"].lower() or search.lower() in doc["filename"].lower()
            ]
        
        if status:
            filtered_docs = [doc for doc in filtered_docs if doc["status"] == status]
            
        if type:
            filtered_docs = [doc for doc in filtered_docs if doc["type"] == type]
        
        # 分页
        start = (page - 1) * limit
        end = start + limit
        paginated_docs = filtered_docs[start:end]
        
        return DocumentResponse(
            success=True,
            data={
                "documents": paginated_docs,
                "total": len(filtered_docs),
                "page": page,
                "limit": limit
            },
            message="获取文档列表成功"
        )
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取文档列表失败")

@router.get("/stats", response_model=DocumentResponse)
async def get_document_stats():
    """获取文档统计信息"""
    try:
        stats = {
            "total_documents": len(MOCK_DOCUMENTS),
            "active_documents": len([d for d in MOCK_DOCUMENTS if d["status"] == "active"]),
            "pending_documents": len([d for d in MOCK_DOCUMENTS if d["status"] == "pending"]),
            "total_size": sum(d["size"] for d in MOCK_DOCUMENTS)
        }
        
        return DocumentResponse(
            success=True,
            data=stats,
            message="获取文档统计成功"
        )
    except Exception as e:
        logger.error(f"获取文档统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取文档统计失败")

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档"""
    try:
        # 模拟文档上传
        new_doc = {
            "id": len(MOCK_DOCUMENTS) + 1,
            "title": file.filename,
            "filename": file.filename,
            "size": file.size or 0,
            "type": file.filename.split('.')[-1] if '.' in file.filename else "unknown",
            "status": "pending",
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        MOCK_DOCUMENTS.append(new_doc)
        
        return DocumentResponse(
            success=True,
            data=new_doc,
            message="文档上传成功"
        )
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(status_code=500, detail="文档上传失败")

@router.put("/{doc_id}/status")
async def update_document_status(doc_id: int, status: str):
    """更新文档状态"""
    try:
        # 模拟更新文档状态
        for doc in MOCK_DOCUMENTS:
            if doc["id"] == doc_id:
                doc["status"] = status
                doc["updated_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return DocumentResponse(
                    success=True,
                    message=f"文档状态已更新为 {status}"
                )
        
        raise HTTPException(status_code=404, detail="文档不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文档状态失败: {e}")
        raise HTTPException(status_code=500, detail="更新文档状态失败")

@router.delete("/{doc_id}")
async def delete_document(doc_id: int):
    """删除文档"""
    try:
        # 模拟删除文档
        for i, doc in enumerate(MOCK_DOCUMENTS):
            if doc["id"] == doc_id:
                MOCK_DOCUMENTS.pop(i)
                return DocumentResponse(
                    success=True,
                    message="文档已删除"
                )
        
        raise HTTPException(status_code=404, detail="文档不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail="删除文档失败")

@router.post("/batch")
async def batch_operation(operation: str, doc_ids: List[int]):
    """批量操作文档"""
    try:
        if operation == "delete":
            # 批量删除
            MOCK_DOCUMENTS[:] = [doc for doc in MOCK_DOCUMENTS if doc["id"] not in doc_ids]
            return DocumentResponse(
                success=True,
                message=f"已批量删除 {len(doc_ids)} 个文档"
            )
        elif operation == "activate":
            # 批量激活
            for doc in MOCK_DOCUMENTS:
                if doc["id"] in doc_ids:
                    doc["status"] = "active"
                    doc["updated_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return DocumentResponse(
                success=True,
                message=f"已批量激活 {len(doc_ids)} 个文档"
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的操作类型")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量操作失败: {e}")
        raise HTTPException(status_code=500, detail="批量操作失败")