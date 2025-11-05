#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建管理员token的脚本
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.admin_user_api import create_access_token
from database.config import get_db_connection
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_admin_token():
    """创建管理员token"""
    try:
        # 使用上下文管理器连接数据库
        with get_db_connection() as conn:
            # 查找第一个用户作为管理员
            admin_query = """
                SELECT id, email, username 
                FROM users 
                ORDER BY id 
                LIMIT 1
            """
            
            cursor = conn.cursor()
            cursor.execute(admin_query)
            admin_user = cursor.fetchone()
            
            if not admin_user:
                logger.error("❌ 没有找到任何用户")
                return None
                
            # 获取列名
            columns = [desc[0] for desc in cursor.description]
            admin_dict = dict(zip(columns, admin_user))
            
            logger.info(f"✅ 找到用户: {admin_dict['username']} ({admin_dict['email']})")
            
            # 创建token，设置为管理员角色
            token_data = {
                "id": admin_dict['id'],
                "email": admin_dict['email'],
                "username": admin_dict['username'],
                "role": "admin"  # 手动设置为管理员
            }
            
            token = create_access_token(token_data)
            
            logger.info(f"🔑 管理员token已创建:")
            logger.info(f"Token: {token}")
            
            # 保存到文件
            with open("admin_token.txt", "w") as f:
                f.write(token)
            
            logger.info("💾 Token已保存到 admin_token.txt 文件")
            
            cursor.close()
            return token
        
    except Exception as e:
        logger.error(f"❌ 创建管理员token失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    create_admin_token()