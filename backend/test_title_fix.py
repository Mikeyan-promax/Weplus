#!/usr/bin/env python3
"""
测试文档标题修复的脚本
"""
import requests
import json

def test_document_titles():
    """测试文档标题显示"""
    print("🔍 测试修复后的文档标题显示...")
    print("=" * 60)
    
    try:
        # 请求文档列表
        response = requests.get("http://localhost:8000/api/rag/documents")
        
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            
            print(f"📊 找到 {len(documents)} 个文档:")
            print()
            
            for i, doc in enumerate(documents, 1):
                print(f"📄 文档 {i}:")
                print(f"   ID: {doc.get('id')}")
                print(f"   标题: '{doc.get('title')}'")
                print(f"   分块数: {doc.get('chunk_count')}")
                print(f"   处理时间: {doc.get('processed_at')}")
                print(f"   内容长度: {doc.get('content_length')}")
                
                # 检查是否还有"未命名文档"
                if doc.get('title') == '未命名文档':
                    print(f"   ❌ 仍然显示为'未命名文档'")
                else:
                    print(f"   ✅ 标题正常显示")
                print()
            
            # 统计未命名文档数量
            unnamed_count = sum(1 for doc in documents if doc.get('title') == '未命名文档')
            if unnamed_count > 0:
                print(f"⚠️  仍有 {unnamed_count} 个文档显示为'未命名文档'")
            else:
                print("✅ 所有文档都有正确的标题")
                
        else:
            print(f"❌ API请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_document_titles()