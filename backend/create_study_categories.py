#!/usr/bin/env python3
import sys
sys.path.append('.')
from database.study_resources_models import execute_query

# 学习资源分类数据
study_categories = [
    {
        'name': '英语四级',
        'code': 'cet4',
        'description': '大学英语四级考试相关学习资源',
        'icon': '📚',
        'color': '#4A90E2'
    },
    {
        'name': '英语六级',
        'code': 'cet6',
        'description': '大学英语六级考试相关学习资源',
        'icon': '📖',
        'color': '#5CB85C'
    },
    {
        'name': '雅思',
        'code': 'ielts',
        'description': '雅思考试相关学习资源',
        'icon': '🌍',
        'color': '#F0AD4E'
    },
    {
        'name': '托福',
        'code': 'toefl',
        'description': '托福考试相关学习资源',
        'icon': '🎓',
        'color': '#D9534F'
    },
    {
        'name': '考研英语',
        'code': 'postgraduate',
        'description': '考研英语相关学习资源',
        'icon': '🎯',
        'color': '#9B59B6'
    },
    {
        'name': '其他语言学习',
        'code': 'other_languages',
        'description': '其他语言学习资源',
        'icon': '🗣️',
        'color': '#17A2B8'
    }
]

try:
    print("开始创建学习资源分类...")
    
    # 首先插入新的学习资源分类
    for i, category in enumerate(study_categories):
        query = """
        INSERT INTO resource_categories (name, code, description, icon, color, sort_order, is_active, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (
            category['name'],
            category['code'],
            category['description'],
            category['icon'],
            category['color'],
            i + 1,  # sort_order
            True    # is_active
        )
        
        execute_query(query, params)
        print(f"创建分类: {category['name']}")
    
    # 获取新创建的第一个分类ID（英语四级）
    new_categories = execute_query('SELECT id FROM resource_categories WHERE code = %s', ('cet4',))
    if new_categories:
        new_category_id = new_categories[0]['id']
        
        # 将现有资源的分类ID更新为新的分类ID
        print("更新现有资源的分类...")
        execute_query("UPDATE study_resources SET category_id = %s WHERE category_id IN (1,2,3,4,5,6,7,8,9)", (new_category_id,))
        
        # 现在可以安全删除旧分类
        print("删除旧分类...")
        execute_query("DELETE FROM resource_categories WHERE id IN (1,2,3,4,5,6,7,8,9)")
    
    print("\n学习资源分类创建完成！")
    
    # 验证创建结果
    categories = execute_query('SELECT id, name, code, description FROM resource_categories ORDER BY sort_order')
    print('\n当前分类:')
    for cat in categories:
        print(f'  ID: {cat["id"]}, 名称: {cat["name"]}, 代码: {cat["code"]}')
        
except Exception as e:
    print('错误:', str(e))