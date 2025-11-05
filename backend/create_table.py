#!/usr/bin/env python3
"""创建user_study_records表"""

from database.db_manager import db_manager

def create_user_study_records_table():
    """创建user_study_records表"""
    try:
        # 读取SQL文件
        with open('create_user_study_records.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句（按分号分割）
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        # 执行每个SQL语句
        for sql in sql_statements:
            if sql:
                print(f"执行SQL: {sql[:100]}...")
                db_manager.execute_query(sql)
                print("✓ 执行成功")
        
        print("\nuser_study_records表创建完成！")
        
        # 验证表是否创建成功
        result = db_manager.execute_query(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'user_study_records'"
        )
        print(f"验证结果: user_study_records表存在 = {len(result) > 0}")
        
    except Exception as e:
        print(f"创建表时出错: {e}")

if __name__ == "__main__":
    create_user_study_records_table()