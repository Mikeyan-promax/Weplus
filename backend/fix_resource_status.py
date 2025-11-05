import psycopg2
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def fix_resource_status():
    try:
        # 连接数据库
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'weplus'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password')
        )
        cursor = conn.cursor()
        
        # 查看当前状态
        cursor.execute("SELECT id, title, status FROM study_resources ORDER BY id")
        resources = cursor.fetchall()
        print("修复前的资源状态:")
        for resource in resources:
            print(f"  ID: {resource[0]}, 标题: {resource[1]}, 状态: {resource[2]}")
        
        # 将所有deleted状态的资源改为active
        cursor.execute("UPDATE study_resources SET status = 'active' WHERE status = 'deleted'")
        updated_count = cursor.rowcount
        conn.commit()
        
        print(f"\n✅ 已将 {updated_count} 个资源的状态从 'deleted' 改为 'active'")
        
        # 查看修复后的状态
        cursor.execute("SELECT id, title, status FROM study_resources ORDER BY id")
        resources = cursor.fetchall()
        print("\n修复后的资源状态:")
        for resource in resources:
            print(f"  ID: {resource[0]}, 标题: {resource[1]}, 状态: {resource[2]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"修复资源状态失败: {e}")

if __name__ == "__main__":
    fix_resource_status()