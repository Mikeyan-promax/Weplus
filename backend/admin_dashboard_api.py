"""
管理员仪表板API模块
提供管理员仪表板数据相关的API接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import logging
from datetime import datetime, timedelta
import random

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/dashboard", tags=["管理员仪表板"])

# 数据模型
class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    total_documents: int
    pending_documents: int
    system_health: str
    storage_usage: float

class SystemActivity(BaseModel):
    timestamp: str
    activity_type: str
    description: str
    user: str

class DashboardResponse(BaseModel):
    success: bool
    data: dict = None
    message: str = ""

def generate_mock_activities() -> List[Dict]:
    """生成模拟系统活动数据"""
    activities = []
    activity_types = ["login", "upload", "delete", "update", "backup"]
    users = ["admin", "user1", "user2", "manager"]
    
    for i in range(10):
        activity = {
            "timestamp": (datetime.now() - timedelta(hours=i)).strftime('%Y-%m-%d %H:%M:%S'),
            "activity_type": random.choice(activity_types),
            "description": f"系统活动 {i+1}",
            "user": random.choice(users)
        }
        activities.append(activity)
    
    return activities

@router.get("/stats", response_model=DashboardResponse)
async def get_dashboard_stats():
    """获取仪表板统计数据"""
    try:
        stats = {
            "total_users": 156,
            "active_users": 89,
            "total_documents": 234,
            "pending_documents": 12,
            "system_health": "healthy",
            "storage_usage": 67.5,
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "disk_usage": 78.3
        }
        
        return DashboardResponse(
            success=True,
            data=stats,
            message="获取仪表板统计成功"
        )
    except Exception as e:
        logger.error(f"获取仪表板统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取仪表板统计失败")

@router.get("/activities", response_model=DashboardResponse)
async def get_recent_activities():
    """获取最近系统活动"""
    try:
        activities = generate_mock_activities()
        
        return DashboardResponse(
            success=True,
            data={"activities": activities},
            message="获取系统活动成功"
        )
    except Exception as e:
        logger.error(f"获取系统活动失败: {e}")
        raise HTTPException(status_code=500, detail="获取系统活动失败")

@router.get("/charts/users", response_model=DashboardResponse)
async def get_user_chart_data():
    """获取用户图表数据"""
    try:
        # 生成过去7天的用户数据
        chart_data = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=6-i)).strftime('%Y-%m-%d %H:%M:%S')
            chart_data.append({
                "date": date,
                "new_users": random.randint(5, 20),
                "active_users": random.randint(50, 100)
            })
        
        return DashboardResponse(
            success=True,
            data={"chart_data": chart_data},
            message="获取用户图表数据成功"
        )
    except Exception as e:
        logger.error(f"获取用户图表数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户图表数据失败")

@router.get("/charts/documents", response_model=DashboardResponse)
async def get_document_chart_data():
    """获取文档图表数据"""
    try:
        # 生成文档类型分布数据
        chart_data = [
            {"type": "PDF", "count": 45, "percentage": 35.2},
            {"type": "Word", "count": 32, "percentage": 25.0},
            {"type": "Excel", "count": 28, "percentage": 21.9},
            {"type": "PowerPoint", "count": 15, "percentage": 11.7},
            {"type": "其他", "count": 8, "percentage": 6.2}
        ]
        
        return DashboardResponse(
            success=True,
            data={"chart_data": chart_data},
            message="获取文档图表数据成功"
        )
    except Exception as e:
        logger.error(f"获取文档图表数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取文档图表数据失败")

@router.get("/system/health", response_model=DashboardResponse)
async def get_system_health():
    """获取系统健康状态"""
    try:
        health_data = {
            "overall_status": "healthy",
            "services": [
                {"name": "数据库", "status": "healthy", "response_time": "12ms"},
                {"name": "文件存储", "status": "healthy", "response_time": "8ms"},
                {"name": "向量存储", "status": "healthy", "response_time": "15ms"},
                {"name": "API服务", "status": "healthy", "response_time": "5ms"}
            ],
            "last_check": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return DashboardResponse(
            success=True,
            data=health_data,
            message="获取系统健康状态成功"
        )
    except Exception as e:
        logger.error(f"获取系统健康状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取系统健康状态失败")