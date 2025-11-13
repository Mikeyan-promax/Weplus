import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import LoadingSpinner from './LoadingSpinner';
import type { Message } from '../types/Message';
import { ragApi, type RAGChatMessage } from '../services/ragApi';
import { getUserData, setUserData, USER_DATA_TYPES } from '../utils/userDataManager';
import { useAuth } from '../contexts/AuthContext';
import './RAGChat.css';

const RAGChat: React.FC = () => {
  const { user } = useAuth();
  
  // 从用户数据中加载聊天历史
  const loadChatHistory = (): Message[] => {
    if (!user) return [];
    
    try {
      const savedHistory = getUserData(USER_DATA_TYPES.CHAT_HISTORY);
      if (savedHistory && Array.isArray(savedHistory)) {
        return savedHistory.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
      }
    } catch (error) {
      console.warn('加载聊天历史失败:', error);
    }
    
    return [];
  };

  // 保存聊天历史到用户数据
  const saveChatHistory = (messages: Message[]) => {
    if (!user) return;
    
    try {
      // 只保存最近50条消息
      const messagesToSave = messages.slice(-50).map(msg => ({
        ...msg,
        timestamp: msg.timestamp.toISOString()
      }));
      setUserData(USER_DATA_TYPES.CHAT_HISTORY, messagesToSave);
    } catch (error) {
      console.warn('保存聊天历史失败:', error);
    }
  };

  const [messages, setMessages] = useState<Message[]>(() => {
    const savedHistory = loadChatHistory();
    if (savedHistory.length > 0) {
      return savedHistory;
    }
    
    // 默认欢迎消息
    return [
      {
        id: '1',
        content: '您好！我是校园智能AI助手，可以帮助您解答关于校园生活、学习资源、校区导航等各种问题。请问有什么可以帮助您的吗？',
        sender: 'assistant',
        timestamp: new Date()
      }
    ];
  });
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [canStop, setCanStop] = useState(false);
  const [abortController, setAbortController] = useState<AbortController | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动调整文本框高度
  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  // 滚动到底部
  /**
   * scrollToBottom
   * 功能：将消息列表滚动到末尾
   * 说明：为避免流式追加期间页面抖动，仅在非生成中（canStop=false）或非加载中（isLoading=false）时触发。
   */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // 在消息变化时：仅保存历史；当非流式状态时才滚动到底部，防止窗口抖动
  useEffect(() => {
    // 保存聊天历史
    saveChatHistory(messages);
    // 非生成中、非加载中时允许自动滚动到底部
    if (!isLoading && !canStop) {
      scrollToBottom();
    }
  }, [messages, isLoading, canStop]);

  // 发送消息 - 使用RAG API
  /**
   * handleSendMessage
   * 功能：发送用户消息并启动流式AI回答；在发送后将右侧按钮切换为“停止”形态
   * 约束：发送期间仅点击“停止”按钮可中断；按下Enter不会停止当前回答
   */
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue.trim();
    setInputValue('');
    setIsLoading(true);
    setCanStop(true);

    // 创建新的AbortController
    const controller = new AbortController();
    setAbortController(controller);

    // 重置文本框高度
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // 创建AI消息占位符
  const assistantMessageId = (Date.now() + 1).toString();
  const assistantMessage: Message = {
    id: assistantMessageId,
    content: '',
    sender: 'assistant',
    timestamp: new Date(),
    isStreaming: true
  };

    setMessages(prev => [...prev, assistantMessage]);

    try {
      // 构建聊天历史
      const chatHistory: RAGChatMessage[] = messages
        .filter(msg => msg.sender !== 'assistant' || msg.content.trim() !== '')
        .map(msg => ({
          role: msg.sender === 'user' ? 'user' : 'assistant',
          content: msg.content
        }));

      // 调用RAG API进行流式聊天
      await ragApi.streamChat(currentInput, chatHistory, (response) => {
        if (response.error) {
          // 如果是用户主动停止，不显示错误信息
          if (response.error === 'Request aborted') {
            setIsLoading(false);
            setCanStop(false);
            setAbortController(null);
            // 取消时关闭紧凑样式
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessageId ? { ...msg, isStreaming: false } : msg
            ));
            return;
          }
          
          // 处理其他错误
          setMessages(prev => prev.map(msg => 
            msg.id === assistantMessageId 
              ? { ...msg, content: `抱歉，服务出现问题：${response.error}` }
              : msg
          ));
          setIsLoading(false);
          setCanStop(false);
          setAbortController(null);
          // 出错时关闭紧凑样式
          setMessages(prev => prev.map(msg => 
            msg.id === assistantMessageId ? { ...msg, isStreaming: false } : msg
          ));
          return;
        }

        if (response.finished) {
          // 流式输出完成
          setIsLoading(false);
          setCanStop(false);
          setAbortController(null);
          // 流式完成后关闭紧凑样式
          setMessages(prev => prev.map(msg => 
            msg.id === assistantMessageId ? { ...msg, isStreaming: false } : msg
          ));
          return;
        }

        // 更新AI消息内容（流式追加）- 优化性能，避免不必要的重新渲染
        if (response.content) {
          setMessages(prev => {
            const newMessages = [...prev];
            const targetIndex = newMessages.findIndex(msg => msg.id === assistantMessageId);
            if (targetIndex !== -1) {
              newMessages[targetIndex] = {
                ...newMessages[targetIndex],
                // 保留原始Markdown内容，避免被压缩规则影响渲染效果
                content: newMessages[targetIndex].content + response.content
              };
            }
            return newMessages;
          });
        }
      }, true, controller);

    } catch (error) {
      console.error('发送消息失败:', error);
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessageId 
          ? { ...msg, content: '抱歉，我现在无法回复您的消息。请稍后再试。' }
          : msg
      ));
      setIsLoading(false);
      setCanStop(false);
      setAbortController(null);
    }
  };

  /**
   * handleStopResponse
   * 功能：主动停止当前AI回答（通过AbortController），并在最后一条AI消息追加“已停止”标记
   * 触发：仅当用户点击“停止”按钮时触发；按Enter不触发停止
   */
  const handleStopResponse = () => {
    if (abortController) {
      abortController.abort();
      setIsLoading(false);
      setCanStop(false);
      setAbortController(null);
      
      // 在最后一条AI消息后添加停止标记
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage && lastMessage.sender === 'assistant') {
          return prev.map((msg, index) => 
            index === prev.length - 1 
              ? { ...msg, content: msg.content + '\n\n[回答已停止]', isStreaming: false }
              : msg
          );
        }
        return prev;
      });
    }
  };

  return (
    <div className="rag-chat">
      <div className="messages-container">
        <div className="messages-list">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {isLoading && (
            <div className="loading-message">
              <div className="message-bubble assistant">
                <LoadingSpinner size="small" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>



      <div className="input-container">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value);
              adjustTextareaHeight();
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                // 需求：在生成中（canStop为true）按Enter不停止也不触发再次发送，保持输出不中断
                if (canStop) {
                  return; // 忽略本次Enter
                }
                // 非生成中，按Enter触发发送
                handleSendMessage();
              }
            }}
            placeholder="输入您的问题... (Shift+Enter 换行)"
            className="message-input"
            disabled={false /* 输入框不禁用；按Enter在生成中被忽略，不会停止 */}
            rows={1}
          />
          
          {/* 发送/停止按钮 */}
          {canStop ? (
            <button
              onClick={handleStopResponse}
              className="stop-button"
              title="停止回答"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor"/>
              </svg>
            </button>
          ) : (
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              className={`send-button ${!inputValue.trim() ? 'disabled' : 'enabled'}`}
              title={!inputValue.trim() ? '请输入消息' : '发送消息'}
            >
              {isLoading ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="loading-icon">
                  <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeDasharray="15 5" strokeDashoffset="0">
                    <animateTransform attributeName="transform" type="rotate" values="0 12 12;360 12 12" dur="1s" repeatCount="indefinite"/>
                  </circle>
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M7 11L12 6L17 11M12 18V7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )}
            </button>
          )}
        </div>
        <div className="input-footer">
          <p className="input-hint">
            💡 提示：由RAG知识库+DeepSeek AI驱动，可以回答专属于中国海洋大学校园生活、学习资源、导航等问题
          </p>
        </div>
      </div>
    </div>
  );
};

export default RAGChat;
