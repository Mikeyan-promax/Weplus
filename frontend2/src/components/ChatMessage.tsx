import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import rehypeKatex from 'rehype-katex';
import type { Message } from '../types/Message';
import 'highlight.js/styles/github.css';
import 'katex/dist/katex.min.css';
import './ChatMessage.css';

export interface ChatMessageProps {
  message: Message;
}

/**
 * ChatMessage 组件（渲染单条聊天消息）
 * 功能说明：
 * - 根据 sender 渲染用户/助手不同气泡与头像
 * - ReactMarkdown 渲染 Markdown（链接、表格、代码、数学公式）
 * - 优化排版：行间距、字间距、标题尺寸、长网址换行、表格与代码不超宽
 */
const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  /**
   * 格式化时间戳为“HH:MM”
   * 仅展示到分钟，保持聊天时间戳简洁
   */
  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  /**
   * 复制到剪贴板
   * 用于代码块复制按钮；失败时在控制台提示错误
   */
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      // 可以添加一个简单的提示
      console.log('已复制到剪贴板:', text);
    }).catch(err => {
      console.error('复制失败:', err);
    });
  };

  // 打字效果组件
  if (message.isTyping) {
    return (
      <div className="chat-message-container assistant">
        <div className="message-avatar assistant-avatar">
          <div className="avatar-icon">🤖</div>
        </div>
        <div className="message-bubble-wrapper">
          <div className="message-bubble assistant-bubble typing-bubble">
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const isUser = message.sender === 'user';
  const isAssistant = message.sender === 'assistant';
  const bubbleClass = `message-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'} ${isAssistant && message.isStreaming ? 'streaming' : ''}`;
  const contentClass = `message-content ${isAssistant && message.isStreaming ? 'streaming' : ''}`;

  return (
    <div className={`chat-message-container ${isUser ? 'user' : 'assistant'}`}>
      {/* 助手头像 */}
      {isAssistant && (
        <div className="message-avatar assistant-avatar">
          <div className="avatar-icon">🤖</div>
        </div>
      )}
      
      <div className="message-bubble-wrapper">
        <div className={bubbleClass}>
          <div className={contentClass}>
            {isAssistant ? (
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[
                  rehypeHighlight, 
                  rehypeRaw, 
                  [rehypeKatex, {
                    strict: false,
                    trust: true,
                    macros: {
                      "\\RR": "\\mathbb{R}",
                      "\\NN": "\\mathbb{N}",
                      "\\ZZ": "\\mathbb{Z}",
                      "\\QQ": "\\mathbb{Q}",
                      "\\CC": "\\mathbb{C}"
                    }
                }]
              ]}
                components={{
                  // 压缩Markdown标题的字号与间距，保持一致性与紧凑感
                  h1: ({ children }) => <h1 className="message-heading h1">{children}</h1>,
                  h2: ({ children }) => <h2 className="message-heading h2">{children}</h2>,
                  h3: ({ children }) => <h3 className="message-heading h3">{children}</h3>,
                  h4: ({ children }) => <h4 className="message-heading h4">{children}</h4>,
                  h5: ({ children }) => <h5 className="message-heading h5">{children}</h5>,
                  h6: ({ children }) => <h6 className="message-heading h6">{children}</h6>,
                  // 自定义代码渲染（含代码块与内联代码）
                  // 函数说明：
                  // - 代码块：保留原始格式与语法高亮，提供复制按钮；禁止随意换行，提供横向滚动容器。
                  // - 内联代码：加上突出显示样式（inline-code），与周围文本区分。
                  code: ({ inline, className, children, ...props }: { inline?: boolean; className?: string; children?: React.ReactNode } & React.HTMLAttributes<HTMLElement>) => {
                    const match = /language-(\w+)/.exec(className || '');
                    const language = match ? match[1] : '';
                     const codeContent = String(children).replace(/\n$/, '');
                     
                     if (!inline && language) {
                       return (
                         <div className="code-block-container">
                           <div className="code-block-header">
                             <span className="code-language">{language}</span>
                             <button
                               className="copy-button"
                               onClick={() => copyToClipboard(codeContent)}
                               title="复制代码"
                             >
                               📋
                             </button>
                           </div>
                           <pre className={className}>
                             <code {...props}>
                               {children}
                             </code>
                           </pre>
                         </div>
                       );
                     }
                     
                     // 行内代码：统一应用突出样式
                     if (inline) {
                       const combinedClass = ['inline-code', className].filter(Boolean).join(' ');
                       return <code className={combinedClass} {...props}>{children}</code>;
                     }
                     
                     return <code className={className} {...props}>{children}</code>;
                  },
                  // 引用块：特殊样式区分，提升可读性
                  blockquote: ({ children }) => <blockquote className="message-blockquote">{children}</blockquote>,
                  // 分割线：风格统一，适当上下间距
                  hr: () => <hr className="message-divider" />,
                  // 自定义段落样式
                  p: ({ children }) => <p className="message-paragraph">{children}</p>,
                  // 自定义列表样式
                  ul: ({ children }) => <ul className="message-list">{children}</ul>,
                  ol: ({ children }) => <ol className="message-list ordered">{children}</ol>,
                  li: ({ children }) => <li className="message-list-item">{children}</li>,
                  // 自定义链接样式
                  a: ({ href, children }) => (
                    <a href={href} className="message-link" target="_blank" rel="noopener noreferrer">
                      {children}
                    </a>
                  ),

                  // 自定义表格样式
                  table: ({ children }) => <table className="message-table">{children}</table>,
                  th: ({ children }) => <th className="message-table-header">{children}</th>,
                  td: ({ children }) => <td className="message-table-cell">{children}</td>,
                }}
              >
                {message.content}
              </ReactMarkdown>
            ) : (
              <div className="user-message-text">{message.content}</div>
            )}
          </div>
        </div>
        
        {/* 时间戳 */}
        <div className={`message-timestamp ${isUser ? 'user-timestamp' : 'assistant-timestamp'}`}>
          {formatTime(message.timestamp)}
        </div>
      </div>

      {/* 用户头像 */}
      {isUser && (
        <div className="message-avatar user-avatar">
          <div className="avatar-icon">👤</div>
        </div>
      )}
    </div>
  );
};

export default ChatMessage;
