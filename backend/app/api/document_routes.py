"""
文档管理API路由
提供文档上传、列表、删除、搜索等功能
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends, Form
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# 本地服务导入
from ..services.document_service import document_service
from ..services.postgresql_vector_service import postgresql_vector_service
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from auth_service import auth_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTTP Bearer 认证
security = HTTPBearer()

# 认证依赖函数
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """验证用户token并返回用户信息"""
    try:
        token = credentials.credentials
        user_info = auth_service.get_user_from_token(token)
        return user_info
    except Exception as e:
        logger.error(f"Token验证失败: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )

# 创建路由器
router = APIRouter(prefix="/api/documents", tags=["documents"])

# 请求模型
class DocumentSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    category: Optional[str] = None
    tags: Optional[List[str]] = None

class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None

class CategoryCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None

class TagCreateRequest(BaseModel):
    name: str
    color: Optional[str] = "#1890ff"
    description: Optional[str] = None

class BatchOperationRequest(BaseModel):
    document_ids: List[int]
    operation: str  # "delete", "categorize", "tag"
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None

class DocumentUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None

# ==================== 文档基础操作 ====================

# 文档上传
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    tags: Optional[str] = Form(None),  # JSON字符串格式的标签ID列表
    current_user: dict = Depends(verify_token)
):
    """
    上传文档
    
    Args:
        file: 上传的文件
        title: 文档标题
        description: 文档描述
        category_id: 分类ID
        tags: 标签ID列表（JSON字符串）
        current_user: 当前用户信息
        
    Returns:
        上传结果
    """
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 解析标签
        tag_list = []
        if tags:
            import json
            try:
                tag_list = json.loads(tags)
            except json.JSONDecodeError:
                logger.warning("标签JSON解析失败，使用空标签列表")
        
        # 构建元数据
        doc_metadata = {
            "title": title or file.filename,
            "description": description,
            "category_id": category_id,
            "tag_ids": tag_list,
            "uploaded_by": current_user.get("user_id"),
            "uploader_email": current_user.get("email")
        }
        
        # 处理文档上传
        result = await document_service.upload_document(
            file_content=file_content,
            filename=file.filename,
            metadata=doc_metadata
        )
        
        if result["success"]:
            logger.info(f"用户 {current_user.get('email')} 上传文档 {file.filename} 成功")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "文档上传成功",
                    "data": result
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": result.get("error", "上传失败"),
                    "data": result
                }
            )
            
    except Exception as e:
        logger.error(f"文档上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

# 批量上传文档
@router.post("/batch-upload")
async def batch_upload_documents(
    files: List[UploadFile] = File(...),
    category_id: Optional[int] = Form(None),
    tags: Optional[str] = Form(None),  # JSON字符串格式的标签ID列表
    current_user: dict = Depends(verify_token)
):
    """
    批量上传文档
    
    Args:
        files: 上传的文件列表
        category_id: 分类ID
        tags: 标签ID列表（JSON字符串）
        current_user: 当前用户信息
        
    Returns:
        批量上传结果
    """
    try:
        # 解析标签
        tag_list = []
        if tags:
            import json
            try:
                tag_list = json.loads(tags)
            except json.JSONDecodeError:
                logger.warning("标签JSON解析失败，使用空标签列表")
        
        results = []
        for file in files:
            try:
                # 读取文件内容
                file_content = await file.read()
                
                # 构建元数据
                doc_metadata = {
                    "title": file.filename,
                    "category_id": category_id,
                    "tag_ids": tag_list,
                    "uploaded_by": current_user.get("user_id"),
                    "uploader_email": current_user.get("email")
                }
                
                # 处理文档上传
                result = await document_service.upload_document(
                    file_content=file_content,
                    filename=file.filename,
                    metadata=doc_metadata
                )
                
                results.append({
                    "filename": file.filename,
                    "success": result["success"],
                    "message": result.get("error") if not result["success"] else "上传成功",
                    "document_id": result.get("document_id") if result["success"] else None
                })
                
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "message": str(e),
                    "document_id": None
                })
        
        success_count = sum(1 for r in results if r["success"])
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"批量上传完成，成功 {success_count}/{len(files)} 个文件",
                "data": {
                    "results": results,
                    "total": len(files),
                    "success_count": success_count,
                    "failed_count": len(files) - success_count
                }
            }
        )
        
    except Exception as e:
        logger.error(f"批量上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")

# 获取文档列表
@router.get("/list")
async def get_documents_list(
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: Optional[int] = Query(None, description="分类ID筛选"),
    tag_ids: Optional[str] = Query(None, description="标签ID列表（逗号分隔）"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: Optional[str] = Query("upload_time", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方向"),
    current_user: dict = Depends(verify_token)
):
    """
    获取文档列表
    
    Args:
        offset: 偏移量
        limit: 每页数量
        category_id: 分类ID筛选
        tag_ids: 标签ID列表
        search: 搜索关键词
        sort_by: 排序字段
        sort_order: 排序方向
        current_user: 当前用户信息
        
    Returns:
        文档列表
    """
    try:
        # 解析标签ID列表
        tag_id_list = []
        if tag_ids:
            try:
                tag_id_list = [int(tid.strip()) for tid in tag_ids.split(",") if tid.strip()]
            except ValueError:
                logger.warning("标签ID解析失败，忽略标签筛选")
        
        result = await document_service.get_document_list(
            offset=offset,
            limit=limit,
            category_id=category_id,
            tag_ids=tag_id_list,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "获取文档列表成功",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")

# 获取文档详情
@router.get("/{document_id}")
async def get_document_detail(
    document_id: int,
    current_user: dict = Depends(verify_token)
):
    """
    获取文档详情
    
    Args:
        document_id: 文档ID
        current_user: 当前用户信息
        
    Returns:
        文档详情
    """
    try:
        result = await document_service.get_document_detail(document_id)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "获取文档详情成功",
                    "data": result
                }
            )
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": result.get("error", "文档不存在"),
                    "data": None
                }
            )
            
    except Exception as e:
        logger.error(f"获取文档详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")

# 更新文档信息
@router.put("/{document_id}")
async def update_document(
    document_id: int,
    request: DocumentUpdateRequest,
    current_user: dict = Depends(verify_token)
):
    """
    更新文档信息
    
    Args:
        document_id: 文档ID
        request: 更新请求
        current_user: 当前用户信息
        
    Returns:
        更新结果
    """
    try:
        result = await document_service.update_document(
            document_id=document_id,
            title=request.title,
            description=request.description,
            category_id=request.category_id,
            tag_ids=request.tag_ids
        )
        
        if result["success"]:
            logger.info(f"用户 {current_user.get('email')} 更新文档 {document_id} 成功")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "文档更新成功",
                    "data": result
                }
            )
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": result.get("error", "更新失败"),
                    "data": result
                }
            )
            
    except Exception as e:
        logger.error(f"更新文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

# 删除文档
@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: dict = Depends(verify_token)
):
    """
    删除文档
    
    Args:
        document_id: 文档ID
        current_user: 当前用户信息
        
    Returns:
        删除结果
    """
    try:
        result = await document_service.delete_document(document_id)
        
        if result["success"]:
            logger.info(f"用户 {current_user.get('email')} 删除文档 {document_id} 成功")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "文档删除成功",
                    "data": result
                }
            )
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": result.get("error", "删除失败"),
                    "data": result
                }
            )
            
    except Exception as e:
        logger.error(f"删除文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

# ==================== 分类管理 ====================

# 创建分类
@router.post("/categories")
async def create_category(
    request: CategoryCreateRequest,
    current_user: dict = Depends(verify_token)
):
    """
    创建文档分类
    
    Args:
        request: 分类创建请求
        current_user: 当前用户信息
        
    Returns:
        创建结果
    """
    try:
        result = await document_service.create_category(
            name=request.name,
            description=request.description,
            parent_id=request.parent_id,
            created_by=current_user.get("user_id")
        )
        
        if result["success"]:
            logger.info(f"用户 {current_user.get('email')} 创建分类 {request.name} 成功")
            return JSONResponse(
                status_code=201,
                content={
                    "success": True,
                    "message": "分类创建成功",
                    "data": result
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": result.get("error", "创建失败"),
                    "data": result
                }
            )
            
    except Exception as e:
        logger.error(f"创建分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建分类失败: {str(e)}")

# 获取分类列表
@router.get("/categories")
async def get_categories(
    include_count: bool = Query(False, description="是否包含文档数量"),
    current_user: dict = Depends(verify_token)
):
    """
    获取分类列表
    
    Args:
        include_count: 是否包含文档数量
        current_user: 当前用户信息
        
    Returns:
        分类列表
    """
    try:
        result = await document_service.get_categories(include_count=include_count)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "获取分类列表成功",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"获取分类列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分类列表失败: {str(e)}")

# 更新分类
@router.put("/categories/{category_id}")
async def update_category(
    category_id: int,
    request: CategoryUpdateRequest,
    current_user: dict = Depends(verify_token)
):
    """
    更新分类信息
    
    Args:
        category_id: 分类ID
        request: 更新请求
        current_user: 当前用户信息
        
    Returns:
        更新结果
    """
    try:
        result = await document_service.update_category(
            category_id=category_id,
            name=request.name,
            description=request.description,
            parent_id=request.parent_id
        )
        
        if result["success"]:
            logger.info(f"用户 {current_user.get('email')} 更新分类 {category_id} 成功")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "分类更新成功",
                    "data": result
                }
            )
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": result.get("error", "更新失败"),
                    "data": result
                }
            )
            
    except Exception as e:
        logger.error(f"更新分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新分类失败: {str(e)}")

# 删除分类
@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    force: bool = Query(False, description="是否强制删除（包含子分类和文档）"),
    current_user: dict = Depends(verify_token)
):
    """
    删除分类
    
    Args:
        category_id: 分类ID
        force: 是否强制删除
        current_user: 当前用户信息
        
    Returns:
        删除结果
    """
    try:
        result = await document_service.delete_category(
            category_id=category_id,
            force=force
        )
        
        if result["success"]:
            logger.info(f"用户 {current_user.get('email')} 删除分类 {category_id} 成功")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "分类删除成功",
                    "data": result
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": result.get("error", "删除失败"),
                    "data": result
                }
            )
            
    except Exception as e:
        logger.error(f"删除分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除分类失败: {str(e)}")

# ==================== 标签管理 ====================

# 创建标签
@router.post("/tags")
async def create_tag(
    request: TagCreateRequest,
    current_user: dict = Depends(verify_token)
):
    """
    创建标签
    
    Args:
        request: 标签创建请求
        current_user: 当前用户信息
        
    Returns:
        创建结果
    """
    try:
        result = await document_service.create_tag(
            name=request.name,
            color=request.color,
            description=request.description,
            created_by=current_user.get("user_id")
        )
        
        if result["success"]:
            logger.info(f"用户 {current_user.get('email')} 创建标签 {request.name} 成功")
            return JSONResponse(
                status_code=201,
                content={
                    "success": True,
                    "message": "标签创建成功",
                    "data": result
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": result.get("error", "创建失败"),
                    "data": result
                }
            )
            
    except Exception as e:
        logger.error(f"创建标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建标签失败: {str(e)}")

# 获取标签列表
@router.get("/tags")
async def get_tags(
    include_count: bool = Query(False, description="是否包含使用次数"),
    current_user: dict = Depends(verify_token)
):
    """
    获取标签列表
    
    Args:
        include_count: 是否包含使用次数
        current_user: 当前用户信息
        
    Returns:
        标签列表
    """
    try:
        result = await document_service.get_tags(include_count=include_count)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "获取标签列表成功",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"获取标签列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标签列表失败: {str(e)}")

# 删除标签
@router.delete("/tags/{tag_id}")
async def delete_tag(
    tag_id: int,
    current_user: dict = Depends(verify_token)
):
    """
    删除标签
    
    Args:
        tag_id: 标签ID
        current_user: 当前用户信息
        
    Returns:
        删除结果
    """
    try:
        result = await document_service.delete_tag(tag_id)
        
        if result["success"]:
            logger.info(f"用户 {current_user.get('email')} 删除标签 {tag_id} 成功")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "标签删除成功",
                    "data": result
                }
            )
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": result.get("error", "删除失败"),
                    "data": result
                }
            )
            
    except Exception as e:
        logger.error(f"删除标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除标签失败: {str(e)}")

# ==================== 批量操作 ====================

# 批量操作
@router.post("/batch-operation")
async def batch_operation(
    request: BatchOperationRequest,
    current_user: dict = Depends(verify_token)
):
    """
    批量操作文档
    
    Args:
        request: 批量操作请求
        current_user: 当前用户信息
        
    Returns:
        操作结果
    """
    try:
        result = await document_service.batch_operation(
            document_ids=request.document_ids,
            operation=request.operation,
            category_id=request.category_id,
            tag_ids=request.tag_ids,
            user_id=current_user.get("user_id")
        )
        
        success_count = result.get("success_count", 0)
        total_count = len(request.document_ids)
        
        logger.info(f"用户 {current_user.get('email')} 批量操作 {request.operation}，成功 {success_count}/{total_count}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"批量操作完成，成功 {success_count}/{total_count} 个文档",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"批量操作失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量操作失败: {str(e)}")

# ==================== 搜索功能 ====================

# 搜索文档
@router.post("/search")
async def search_documents(
    request: DocumentSearchRequest,
    current_user: dict = Depends(verify_token)
):
    """
    搜索文档
    
    Args:
        request: 搜索请求
        current_user: 当前用户信息
        
    Returns:
        搜索结果
    """
    try:
        result = await document_service.search_documents(
            query=request.query,
            top_k=request.top_k,
            category=request.category,
            tags=request.tags
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "文档搜索成功",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"文档搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

# ==================== 分类管理 ====================

# 分类管理请求模型
class CategoryCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None

class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

# 创建分类
@router.post("/categories")
async def create_category(
    request: CategoryCreateRequest,
    current_user: dict = Depends(verify_token)
):
    """
    创建分类
    
    Args:
        request: 分类创建请求
        current_user: 当前用户信息
        
    Returns:
        创建的分类信息
    """
    try:
        result = document_service.create_category(
            name=request.name,
            description=request.description,
            color=request.color
        )
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "分类创建成功",
                "data": result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建分类失败: {str(e)}")

# 获取分类列表
@router.get("/categories")
async def get_categories(
    current_user: dict = Depends(verify_token)
):
    """
    获取所有分类
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        分类列表
    """
    try:
        result = document_service.get_categories()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "获取分类列表成功",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"获取分类列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分类列表失败: {str(e)}")

# 更新分类
@router.put("/categories/{category_id}")
async def update_category(
    category_id: int,
    request: CategoryUpdateRequest,
    current_user: dict = Depends(verify_token)
):
    """
    更新分类
    
    Args:
        category_id: 分类ID
        request: 分类更新请求
        current_user: 当前用户信息
        
    Returns:
        更新后的分类信息
    """
    try:
        result = document_service.update_category(
            category_id=category_id,
            name=request.name,
            description=request.description,
            color=request.color
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "分类更新成功",
                "data": result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新分类失败: {str(e)}")

# 删除分类
@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    current_user: dict = Depends(verify_token)
):
    """
    删除分类
    
    Args:
        category_id: 分类ID
        current_user: 当前用户信息
        
    Returns:
        删除结果
    """
    try:
        result = document_service.delete_category(category_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": result["message"],
                "data": None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除分类失败: {str(e)}")

# ==================== 标签管理 ====================

# 标签管理请求模型
class TagCreateRequest(BaseModel):
    name: str
    color: Optional[str] = None

# 创建标签
@router.post("/tags")
async def create_tag(
    request: TagCreateRequest,
    current_user: dict = Depends(verify_token)
):
    """
    创建标签
    
    Args:
        request: 标签创建请求
        current_user: 当前用户信息
        
    Returns:
        创建的标签信息
    """
    try:
        result = document_service.create_tag(
            name=request.name,
            color=request.color
        )
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "标签创建成功",
                "data": result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建标签失败: {str(e)}")

# 获取标签列表
@router.get("/tags")
async def get_tags(
    current_user: dict = Depends(verify_token)
):
    """
    获取所有标签
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        标签列表
    """
    try:
        result = document_service.get_tags()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "获取标签列表成功",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"获取标签列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标签列表失败: {str(e)}")

# 删除标签
@router.delete("/tags/{tag_id}")
async def delete_tag(
    tag_id: int,
    current_user: dict = Depends(verify_token)
):
    """
    删除标签
    
    Args:
        tag_id: 标签ID
        current_user: 当前用户信息
        
    Returns:
        删除结果
    """
    try:
        result = document_service.delete_tag(tag_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": result["message"],
                "data": None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除标签失败: {str(e)}")

# ==================== 高级搜索 ====================

# 高级搜索
@router.get("/advanced-search")
async def advanced_search_documents(
    search_term: Optional[str] = Query(None, description="搜索关键词"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    tag_ids: Optional[str] = Query(None, description="标签ID列表（逗号分隔）"),
    file_type: Optional[str] = Query(None, description="文件类型"),
    status: Optional[str] = Query(None, description="文档状态"),
    date_from: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(verify_token)
):
    """
    高级搜索文档
    
    Args:
        search_term: 搜索关键词
        category_id: 分类ID
        tag_ids: 标签ID列表
        file_type: 文件类型
        status: 文档状态
        date_from: 开始日期
        date_to: 结束日期
        page: 页码
        limit: 每页数量
        current_user: 当前用户信息
        
    Returns:
        搜索结果
    """
    try:
        # 解析标签ID列表
        tag_id_list = []
        if tag_ids:
            try:
                tag_id_list = [int(tid.strip()) for tid in tag_ids.split(",") if tid.strip()]
            except ValueError:
                logger.warning("标签ID解析失败，忽略标签筛选")
        
        result = document_service.advanced_search(
            search_term=search_term,
            category_id=category_id,
            tag_ids=tag_id_list,
            file_type=file_type,
            status=status,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "搜索成功",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"高级搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

# ==================== 统计和健康检查 ====================

# 获取文档统计信息
@router.get("/stats/overview")
async def get_documents_stats(
    current_user: dict = Depends(verify_token)
):
    """
    获取文档统计信息
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        统计信息
    """
    try:
        result = await document_service.get_stats()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "获取统计信息成功",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

# 向量存储健康检查
@router.get("/vector-store/health")
async def check_vector_store_health(
    current_user: dict = Depends(verify_token)
):
    """
    检查向量存储健康状态
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        健康状态
    """
    try:
        result = await postgresql_vector_service.health_check()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "健康检查完成",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

# 向量存储统计信息
@router.get("/vector-store/stats")
async def get_vector_store_stats(
    current_user: dict = Depends(verify_token)
):
    """
    获取向量存储统计信息
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        统计信息
    """
    try:
        result = await postgresql_vector_service.get_stats()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "获取向量存储统计成功",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"获取向量存储统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

# 文档服务健康检查
@router.get("/health")
async def check_document_service_health():
    """
    检查文档服务健康状态
    
    Returns:
        健康状态
    """
    try:
        result = await document_service.health_check()
        
        status_code = 200 if result.get("overall", False) else 503
        
        return JSONResponse(
            status_code=status_code,
            content={
                "success": result.get("overall", False),
                "message": "文档服务健康检查完成",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"文档服务健康检查失败: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": "健康检查失败",
                "data": {"error": str(e)}
            }
        )