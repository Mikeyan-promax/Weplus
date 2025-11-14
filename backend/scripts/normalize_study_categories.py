#!/usr/bin/env python3
import sys
sys.path.append('.')
sys.path.append('backend')
from database.study_resources_models import execute_query

normalized = [
    {
        'code': 'cet4',
        'name': '英语四级',
        'description': '大学英语四级考试相关学习资料',
        'icon': '📘',
        'color': '#4A90E2',
        'sort_order': 1
    },
    {
        'code': 'cet6',
        'name': '英语六级',
        'description': '大学英语六级考试相关学习资料',
        'icon': '📙',
        'color': '#5CB85C',
        'sort_order': 2
    },
    {
        'code': 'ielts',
        'name': '雅思备考资料',
        'description': '雅思考试备考资料，涵盖听说读写四个模块',
        'icon': '🌍',
        'color': '#7ED321',
        'sort_order': 2
    },
    {
        'code': 'postgraduate',
        'name': '考研资料',
        'description': '研究生入学考试资料，包括英语、政治、数学、专业课',
        'icon': '📖',
        'color': '#F5A623',
        'sort_order': 3
    },
    {
        'code': 'professional',
        'name': '专业课程资料',
        'description': '各专业核心课程学习资料、实验指导、课件PPT等',
        'icon': '📚',
        'color': '#BD10E0',
        'sort_order': 4
    },
    {
        'code': 'software',
        'name': '软件技能学习',
        'description': '编程语言、开发工具、软件应用等技能学习教程与资料',
        'icon': '💻',
        'color': '#50E3C2',
        'sort_order': 5
    },
    {
        'code': 'academic',
        'name': '学术论文写作指导',
        'description': '学术论文写作、研究方法与规范相关资源',
        'icon': '✍️',
        'color': '#FF6B6B',
        'sort_order': 6
    }
]

old_to_new = {
    'cet4': 'cet4', 'cet6': 'cet6', 'cet': 'cet4',
    'ielts': 'ielts', '雅思': 'ielts', 'toefl': 'ielts',
    'postgraduate': 'postgraduate', 'postgrad': 'postgraduate', '考研英语': 'postgraduate',
    'professional': 'professional', '课程': 'professional', 'others': 'professional',
    'software': 'software', 'code': 'software', '编程学习': 'software', 'programming': 'software',
    'academic': 'academic', '学术写作': 'academic'
}

def upsert_category(cat):
    row = execute_query('SELECT id FROM resource_categories WHERE code = %s', (cat['code'],), fetch_one=True)
    if row:
        execute_query(
            'UPDATE resource_categories SET name = %s, description = %s, icon = %s, color = %s, sort_order = %s, is_active = TRUE, updated_at = NOW() WHERE code = %s',
            (cat['name'], cat['description'], cat['icon'], cat['color'], cat['sort_order'], cat['code']),
            fetch_all=False
        )
    else:
        execute_query(
            'INSERT INTO resource_categories (name, code, description, icon, color, sort_order, is_active, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, TRUE, NOW(), NOW())',
            (cat['name'], cat['code'], cat['description'], cat['icon'], cat['color'], cat['sort_order']),
            fetch_all=False
        )

def get_code_id_map(codes):
    placeholders = ','.join(['%s'] * len(codes))
    rows = execute_query(f'SELECT id, code FROM resource_categories WHERE code IN ({placeholders})', tuple(codes))
    return {r['code']: r['id'] for r in rows}

def merge_categories():
    for cat in normalized:
        upsert_category(cat)
    code_id = get_code_id_map([c['code'] for c in normalized])

    # 将旧分类映射到新分类ID
    for old_code, new_code in old_to_new.items():
        old_rows = execute_query('SELECT id FROM resource_categories WHERE code = %s', (old_code,))
        if not old_rows:
            continue
        old_id = old_rows[0]['id']
        # 特殊拆分逻辑：旧代码为 'cet' 时，根据资源标题/文件名判断分配到 cet4 或 cet6
        if old_code == 'cet':
            rows = execute_query(
                'SELECT sr.id, sr.name, sr.file_name FROM study_resources sr WHERE sr.category_id = %s',
                (old_id,)
            )
            cet4_id = code_id.get('cet4')
            cet6_id = code_id.get('cet6')
            for r in rows:
                name = (r.get('name') or '') + ' ' + (r.get('file_name') or '')
                lower = name.lower()
                is_six = ('cet6' in lower) or ('六级' in name) or ('cetc6' in lower) or ('6级' in name)
                target_id = cet6_id if is_six else cet4_id
                if target_id:
                    execute_query('UPDATE study_resources SET category_id = %s WHERE id = %s', (target_id, r['id']), fetch_all=False)
            # 旧 'cet' 分类置为不激活
            execute_query('UPDATE resource_categories SET is_active = FALSE, updated_at = NOW() WHERE id = %s', (old_id,), fetch_all=False)
            continue
        # 其它旧代码直接映射
        new_id = code_id.get(new_code)
        if not new_id:
            continue
        execute_query('UPDATE study_resources SET category_id = %s WHERE category_id = %s', (new_id, old_id), fetch_all=False)
        if old_code != new_code:
            execute_query('UPDATE resource_categories SET is_active = FALSE, updated_at = NOW() WHERE id = %s', (old_id,), fetch_all=False)

    # 统一名称与展示信息
    for cat in normalized:
        execute_query(
            'UPDATE resource_categories SET name = %s, description = %s, icon = %s, color = %s, sort_order = %s, is_active = TRUE WHERE code = %s',
            (cat['name'], cat['description'], cat['icon'], cat['color'], cat['sort_order'], cat['code']),
            fetch_all=False
        )

if __name__ == '__main__':
    merge_categories()
    result = execute_query('SELECT id, name, code, description, icon, color, sort_order, is_active FROM resource_categories ORDER BY sort_order, name')
    print('统一后的分类:')
    for r in result:
        print(f"{r['id']:>3}  {r['code']:<14}  {r['name']}")
