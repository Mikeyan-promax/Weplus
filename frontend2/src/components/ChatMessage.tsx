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

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 复制到剪贴板的函数
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

  return (
    <div className={`chat-message-container ${isUser ? 'user' : 'assistant'}`}>
      {/* 助手头像 */}
      {isAssistant && (
        <div className="message-avatar assistant-avatar">
          <div className="avatar-icon">🤖</div>
        </div>
      )}
      
      <div className="message-bubble-wrapper">
        <div className={`message-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}>
          <div className="message-content">
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
                  // 自定义代码块渲染，添加复制按钮
                  code: ({ node, inline, className, children, ...props }: any) => {
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
                     
                     // 行内代码或数学公式
                     if (inline) {
                       // 检查是否是数学公式
                       const content = String(children);
                       if (content.startsWith('$') && content.endsWith('$') && content.length > 2) {
                         const mathContent = content.slice(1, -1);
                         return (
                           <span 
                             className="math-inline"
                             onClick={() => copyToClipboard(mathContent)}
                             title="点击复制公式"
                             style={{ cursor: 'pointer' }}
                           >
                             <code {...props}>{children}</code>
                           </span>
                         );
                       }
                     }
                     
                     return <code className={className} {...props}>{children}</code>;
                  },
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