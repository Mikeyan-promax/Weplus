// RAG API 服务
export interface RAGChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface RAGChatRequest {
  message: string;
  history?: RAGChatMessage[];
  use_rag?: boolean;
}

export interface RAGChatResponse {
  response: string;
  sources_used?: Array<{
    document_id: string;
    content: string;
    similarity: number;
  }>;
  error?: string;
}

export interface StreamResponse {
  content: string;
  finished: boolean;
  error?: string;
}

class RAGApiService {
  private baseUrl = 'http://localhost:8000';

  // 真正的流式聊天，使用Server-Sent Events处理DeepSeek的实时响应
  async streamChat(
    message: string,
    history: RAGChatMessage[] = [],
    onChunk: (response: StreamResponse) => void,
    useRAG: boolean = true,
    abortController?: AbortController
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/rag/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          conversation_history: history,
          use_rag: useRAG
        }),
        signal: abortController?.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('无法获取响应流');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          // 检查是否被取消
          if (abortController?.signal.aborted) {
            onChunk({ content: '', finished: true, error: 'Request aborted' });
            return;
          }

          const { done, value } = await reader.read();
          
          if (done) {
            break;
          }

          // 解码数据块
          buffer += decoder.decode(value, { stream: true });
          
          // 处理Server-Sent Events格式的数据
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // 保留最后一个不完整的行

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const jsonStr = line.slice(6); // 移除 'data: ' 前缀
                const data = JSON.parse(jsonStr);
                
                if (data.error) {
                  onChunk({ content: '', finished: true, error: data.error });
                  return;
                }
                
                if (data.finished) {
                  onChunk({ content: '', finished: true });
                  return;
                }
                
                if (data.content) {
                  onChunk({ content: data.content, finished: false });
                }
              } catch (parseError) {
                console.warn('解析SSE数据失败:', parseError, 'Line:', line);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
      
    } catch (error) {
      console.error('RAG流式API调用失败:', error);
      if (error instanceof Error && error.name === 'AbortError') {
        onChunk({ content: '', finished: true, error: 'Request aborted' });
      } else {
        onChunk({ 
          content: '', 
          finished: true, 
          error: error instanceof Error ? error.message : '网络请求失败' 
        });
      }
    }
  }

  // 普通聊天（非流式）
  async chat(
    message: string,
    history: RAGChatMessage[] = [],
    useRAG: boolean = true
  ): Promise<RAGChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/rag/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          conversation_history: history,
          use_rag: useRAG
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json() as RAGChatResponse;
    } catch (error) {
      console.error('RAG API调用失败:', error);
      return {
        response: '',
        error: error instanceof Error ? error.message : '网络请求失败'
      };
    }
  }

  // 获取RAG系统统计信息
  async getStats() {
    try {
      const response = await fetch(`${this.baseUrl}/api/rag/stats`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('获取RAG统计信息失败:', error);
      throw error;
    }
  }

  // 获取已处理的文档列表
  async getDocuments() {
    try {
      const response = await fetch(`${this.baseUrl}/api/rag/documents`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('获取文档列表失败:', error);
      throw error;
    }
  }
}

export const ragApi = new RAGApiService();
export default ragApi;