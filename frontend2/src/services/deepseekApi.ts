// DeepSeek API 服务
// 实现流式聊天功能，类似DeepSeek官网的体验

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface StreamResponse {
  content: string;
  finished: boolean;
  error?: string;
}

class DeepSeekApiService {
  private apiKey: string;
  private baseUrl: string;

  constructor() {
    // 使用你提供的DeepSeek API配置
    this.apiKey = 'sk-9189176321ae486c8f755145b59299eb';
    this.baseUrl = 'https://api.deepseek.com';
  }

  /**
   * 发送流式聊天请求到DeepSeek API
   * @param messages 聊天消息历史
   * @param onChunk 接收流式数据的回调函数
   */
  async streamChat(
    messages: ChatMessage[],
    onChunk: (response: StreamResponse) => void
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify({
          model: 'deepseek-chat',
          messages: [
            {
              role: 'system',
              content: '你是WePlus校园智能AI助手，专门为校园用户提供帮助。你可以回答关于校园生活、学习资源、校区导航、食堂信息、图书馆服务、宿舍管理等各种校园相关问题。请用友好、专业的语气回答用户问题。'
            },
            ...messages
          ],
          stream: true, // 启用流式输出
          max_tokens: 4000,
          temperature: 0.7,
        }),
      });

      if (!response.ok) {
        throw new Error(`DeepSeek API请求失败: ${response.status} ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('无法获取响应流');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          // 流结束
          onChunk({ content: '', finished: true });
          break;
        }

        // 解码数据块
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 保留不完整的行

        for (const line of lines) {
          if (line.trim() === '') continue;
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            if (data === '[DONE]') {
              onChunk({ content: '', finished: true });
              return;
            }

            try {
              const parsed = JSON.parse(data);
              const content = parsed.choices?.[0]?.delta?.content || '';
              
              if (content) {
                onChunk({ content, finished: false });
              }
            } catch (e) {
              console.warn('解析SSE数据失败:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('DeepSeek API调用失败:', error);
      onChunk({
        content: '',
        finished: true,
        error: error instanceof Error ? error.message : '未知错误'
      });
    }
  }

  /**
   * 非流式聊天请求（备用方案）
   */
  async chat(messages: ChatMessage[]): Promise<string> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify({
          model: 'deepseek-chat',
          messages: [
            {
              role: 'system',
              content: '你是WePlus校园智能AI助手，专门为校园用户提供帮助。'
            },
            ...messages
          ],
          stream: false,
          max_tokens: 4000,
          temperature: 0.7,
        }),
      });

      if (!response.ok) {
        throw new Error(`API请求失败: ${response.status}`);
      }

      const data = await response.json();
      return data.choices?.[0]?.message?.content || '抱歉，我无法生成回复。';
    } catch (error) {
      console.error('DeepSeek API调用失败:', error);
      return '抱歉，服务暂时不可用，请稍后再试。';
    }
  }
}

// 导出单例实例
export const deepseekApi = new DeepSeekApiService();