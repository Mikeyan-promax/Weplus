export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  isTyping?: boolean;
  /** 流式阶段紧凑样式标记（函数级注释）：当为true时，前端在渲染时应用更紧凑的行距与间距 */
  isStreaming?: boolean;
}
