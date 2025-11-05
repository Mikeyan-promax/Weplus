#!/usr/bin/env python3
"""
修复embedding维度问题
清理错误维度的数据，重新生成正确的embedding
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def fix_embedding_dimension():
    """修复embedding维度问题"""
    print("🔧 修复embedding维度问题...")
    
    # 数据库配置
    config = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    try:
        conn = await asyncpg.connect(**config)
        print("✅ 连接PostgreSQL成功")
        
        # 1. 检查当前数据
        print("\n📊 检查当前数据...")
        
        # 检查所有chunks的embedding维度
        chunks = await conn.fetch("""
            SELECT id, document_id, chunk_index, 
                   vector_dims(embedding) as dimension,
                   length(content) as content_length,
                   substring(content, 1, 50) as content_preview
            FROM document_chunks 
            WHERE embedding IS NOT NULL
            ORDER BY id;
        """)
        
        print(f"📝 发现 {len(chunks)} 条有embedding的记录:")
        dimension_stats = {}
        for chunk in chunks:
            dim = chunk['dimension']
            if dim not in dimension_stats:
                dimension_stats[dim] = 0
            dimension_stats[dim] += 1
            print(f"  ID {chunk['id']}: {dim}维 - {chunk['content_preview']}...")
        
        print(f"\n📏 维度统计:")
        for dim, count in dimension_stats.items():
            print(f"  {dim}维: {count} 条记录")
        
        # 2. 检查documents表
        print("\n📄 检查documents表...")
        docs = await conn.fetch("SELECT * FROM documents ORDER BY id;")
        print(f"📊 documents表: {len(docs)} 条记录")
        for doc in docs:
            print(f"  - {doc['id']}: {doc['title']} ({doc['file_type']})")
        
        # 3. 清理错误数据的选择
        print(f"\n🤔 发现问题:")
        print(f"  - 期望维度: 2560 (豆包模型)")
        print(f"  - 实际维度: {list(dimension_stats.keys())}")
        print(f"  - 这些数据可能来自之前的其他embedding模型")
        
        # 询问是否清理
        print(f"\n💡 建议操作:")
        print(f"1. 清理所有错误维度的embedding数据")
        print(f"2. 保留文档内容和chunks结构")
        print(f"3. 重新生成正确的2560维embedding")
        
        # 执行清理
        print(f"\n🧹 开始清理错误维度的embedding...")
        
        # 将所有embedding设为NULL，保留其他数据
        update_result = await conn.execute("""
            UPDATE document_chunks 
            SET embedding = NULL 
            WHERE vector_dims(embedding) != 2560;
        """)
        
        print(f"✅ 已清理embedding数据")
        
        # 检查清理后的状态
        remaining_embeddings = await conn.fetchval("""
            SELECT COUNT(*) FROM document_chunks 
            WHERE embedding IS NOT NULL;
        """)
        
        total_chunks = await conn.fetchval("""
            SELECT COUNT(*) FROM document_chunks;
        """)
        
        print(f"📊 清理后状态:")
        print(f"  - 总chunks: {total_chunks}")
        print(f"  - 有embedding的chunks: {remaining_embeddings}")
        print(f"  - 需要重新生成embedding的chunks: {total_chunks - remaining_embeddings}")
        
        # 4. 检查表结构是否需要修改
        print(f"\n🔍 检查表结构...")
        
        # 检查embedding列的定义
        column_info = await conn.fetch("""
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks' 
            AND column_name = 'embedding';
        """)
        
        if column_info:
            print(f"📋 embedding列信息:")
            for col in column_info:
                print(f"  类型: {col['data_type']} ({col['udt_name']})")
        
        # 检查vector类型的维度限制
        try:
            # 尝试插入2560维的测试向量
            test_vector = [0.1] * 2560
            await conn.execute("""
                INSERT INTO document_chunks 
                (document_id, chunk_index, content, embedding) 
                VALUES ('test', 0, 'test content', $1::vector)
                ON CONFLICT DO NOTHING;
            """, test_vector)
            
            # 删除测试数据
            await conn.execute("""
                DELETE FROM document_chunks 
                WHERE document_id = 'test' AND content = 'test content';
            """)
            
            print(f"✅ 表结构支持2560维向量")
            
        except Exception as e:
            print(f"❌ 表结构不支持2560维向量: {e}")
            print(f"💡 可能需要重新创建表或修改vector列定义")
        
        await conn.close()
        print(f"\n✅ 修复完成！")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

async def main():
    """主函数"""
    print("🚀 Embedding维度修复工具")
    print("=" * 50)
    
    success = await fix_embedding_dimension()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 维度修复完成！")
        print("\n💡 下一步:")
        print("1. 重新上传文档，生成正确的2560维embedding")
        print("2. 或者使用API重新处理现有文档")
        print("3. 测试RAG搜索功能")
    else:
        print("❌ 维度修复失败")

if __name__ == "__main__":
    asyncio.run(main())