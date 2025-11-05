import React from 'react';
import ChatMessage from './ChatMessage';
import type { Message } from '../types/Message';
import './RAGChat.css';

const ChatUITest: React.FC = () => {
  /**
   * 测试消息数据：
   * - 使用 Message 类型，满足 ChatMessageProps 要求
   * - timestamp 为 Date 类型，sender 为 'user' | 'assistant'
   */
  const testMessages: Message[] = [
    {
      id: '1',
      content: '你好！我是WePlus智能助手，有什么可以帮助您的吗？',
      sender: 'assistant',
      timestamp: new Date(Date.now() - 300000)
    },
    {
      id: '2',
      content: '请帮我介绍一下Markdown的基本语法',
      sender: 'user',
      timestamp: new Date(Date.now() - 240000)
    },
    {
      id: '3',
      content: `# Markdown基本语法介绍

Markdown是一种轻量级标记语言，以下是常用语法：

## 标题
使用 \`#\` 来创建标题：
- \`# 一级标题\`
- \`## 二级标题\`
- \`### 三级标题\`

## 文本格式
- **粗体文本**：使用 \`**文本**\`
- *斜体文本*：使用 \`*文本*\`
- ~~删除线~~：使用 \`~~文本~~\`

## 列表
### 无序列表
- 项目1
- 项目2
  - 子项目2.1
  - 子项目2.2

### 有序列表
1. 第一项
2. 第二项
3. 第三项

## 代码
### 行内代码
使用 \`console.log('Hello World')\` 来显示行内代码。

### 代码块
\`\`\`javascript
function greet(name) {
  console.log(\`Hello, \${name}!\`);
}

greet('World');
\`\`\`

\`\`\`python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
\`\`\`

## 链接和图片
- [链接文本](https://www.example.com)
- ![图片描述](https://via.placeholder.com/150)

## 表格
| 功能 | 语法 | 示例 |
|------|------|------|
| 粗体 | \`**text**\` | **粗体** |
| 斜体 | \`*text*\` | *斜体* |
| 代码 | \`\`code\`\` | \`code\` |

## 引用
> 这是一个引用块
> 
> 可以包含多行内容
> > 嵌套引用

希望这个介绍对您有帮助！`,
      sender: 'assistant',
      timestamp: new Date(Date.now() - 180000)
    },
    {
      id: '4',
      content: '太棒了！能再展示一些数学公式的例子吗？',
      sender: 'user',
      timestamp: new Date(Date.now() - 120000)
    },
    {
      id: '5',
      content: `当然可以！以下是一些数学公式的示例：

## 行内数学公式
这是一个行内公式：$E = mc^2$，爱因斯坦的质能方程。

## 块级数学公式
### 二次方程求根公式
$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$

### 积分公式
$$\\int_{a}^{b} f(x)dx = F(b) - F(a)$$

### 矩阵
$$\\begin{pmatrix}
a & b \\\\
c & d
\\end{pmatrix}$$

### 求和公式
$$\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}$$

这些公式在学术和工程领域都很常用！`,
      sender: 'assistant',
      timestamp: new Date(Date.now() - 60000)
    },
    {
      id: '6',
      content: '非常感谢！这个聊天界面看起来很棒 👍',
      sender: 'user',
      timestamp: new Date()
    }
  ];

  return (
    <div className="rag-chat">
      <div className="chat-header">
        <h2>聊天UI测试页面</h2>
        <p>测试新的聊天气泡样式和Markdown渲染效果</p>
      </div>
      
      <div className="messages-container">
        {testMessages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        
        {/* 打字指示器测试 */}
        <ChatMessage
          message={{
            id: 'typing',
            content: '',
            sender: 'assistant',
            timestamp: new Date(),
            isTyping: true
          }}
        />
      </div>
    </div>
  );
};

export default ChatUITest;
