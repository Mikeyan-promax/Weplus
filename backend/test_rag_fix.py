#!/usr/bin/env python3
"""
测试RAG聊天功能修复
"""

import asyncio
import aiohttp
import json

async def test_rag_chat():
    """测试RAG聊天功能"""
    
    # 测试数据
    test_cases = [
        {
            "message": "海大有什么特色专业？",
            "use_rag": True,
            "description": "RAG模式 - 询问海大专业信息"
        },
        {
            "message": "你好，请介绍一下自己",
            "use_rag": False,
            "description": "普通模式 - 基础对话"
        },
        {
            "message": "校园里有哪些学习资源？",
            "use_rag": True,
            "description": "RAG模式 - 询问学习资源"
        }
    ]
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print("=== 测试RAG聊天功能修复 ===\n")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"测试 {i}: {test_case['description']}")
            print(f"消息: {test_case['message']}")
            print(f"RAG模式: {test_case['use_rag']}")
            
            # 准备请求数据
            request_data = {
                "message": test_case["message"],
                "conversation_history": [],
                "use_rag": test_case["use_rag"]
            }
            
            try:
                # 发送请求到流式聊天接口
                async with session.post(
                    f"{base_url}/api/rag/chat/stream",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        print("✅ 请求成功")
                        
                        # 读取流式响应
                        response_content = ""
                        async for line in response.content:
                            line_text = line.decode('utf-8').strip()
                            if line_text.startswith('data: '):
                                try:
                                    data = json.loads(line_text[6:])  # 移除 'data: ' 前缀
                                    
                                    if data.get('error'):
                                        print(f"❌ 错误: {data['error']}")
                                        break
                                    
                                    if data.get('content'):
                                        response_content += data['content']
                                        print(".", end="", flush=True)  # 显示进度
                                    
                                    if data.get('finished'):
                                        print("\n✅ 响应完成")
                                        break
                                        
                                except json.JSONDecodeError as e:
                                    print(f"⚠️ 解析响应数据失败: {e}")
                                    continue
                        
                        print(f"📝 完整响应: {response_content[:200]}{'...' if len(response_content) > 200 else ''}")
                        
                    else:
                        print(f"❌ 请求失败，状态码: {response.status}")
                        error_text = await response.text()
                        print(f"错误信息: {error_text}")
                        
            except Exception as e:
                print(f"❌ 请求异常: {str(e)}")
            
            print("-" * 60)
        
        print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_rag_chat())