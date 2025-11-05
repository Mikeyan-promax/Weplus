#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查用户表结构的脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.config import get_db_connection
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_user_table():
    """检查用户表结构"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 检查表结构
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            
            logger.info("📋 用户表结构:")
            for col in columns:
                logger.info(f"  - {col[0]}: {col[1]} (可空: {col[2]}, 默认值: {col[3]})")
            
            # 查看一些用户数据
            cursor.execute("SELECT id, email, username FROM users LIMIT 5")
            users = cursor.fetchall()
            
            logger.info("\n👥 用户数据示例:")
            for user in users:
                logger.info(f"  - ID: {user[0]}, 邮箱: {user[1]}, 用户名: {user[2]}")
            
            cursor.close()
            
    except Exception as e:
        logger.error(f"❌ 检查用户表失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_user_table()