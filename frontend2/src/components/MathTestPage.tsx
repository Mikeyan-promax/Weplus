import React, { useState } from 'react';
import ChatMessage from './ChatMessage';
import type { Message } from '../types/Message';

const MathTestPage: React.FC = () => {
  const [testMessages] = useState<Message[]>([
    {
      id: '1',
      content: '这是行内数学公式测试：$E = mc^2$ 和 $\\sqrt{x^2 + y^2}$',
      sender: 'assistant',
      timestamp: new Date(),
    },
    {
      id: '6',
      content: `高级数学公式测试：

**矩阵运算：**
$$\\begin{bmatrix}
1 & 2 & 3 \\\\
4 & 5 & 6 \\\\
7 & 8 & 9
\\end{bmatrix}
\\times
\\begin{bmatrix}
x \\\\
y \\\\
z
\\end{bmatrix}
=
\\begin{bmatrix}
x + 2y + 3z \\\\
4x + 5y + 6z \\\\
7x + 8y + 9z
\\end{bmatrix}$$

**多重积分：**
$$\\iiint_V f(x,y,z) \\, dx \\, dy \\, dz = \\int_0^1 \\int_0^{\\sqrt{1-x^2}} \\int_0^{\\sqrt{1-x^2-y^2}} f(x,y,z) \\, dz \\, dy \\, dx$$

**级数展开：**
$$\\sin(x) = \\sum_{n=0}^{\\infty} \\frac{(-1)^n x^{2n+1}}{(2n+1)!} = x - \\frac{x^3}{3!} + \\frac{x^5}{5!} - \\frac{x^7}{7!} + \\cdots$$

**复数表示：**
$$e^{i\\theta} = \\cos(\\theta) + i\\sin(\\theta)$$

**偏微分方程：**
$$\\frac{\\partial^2 u}{\\partial t^2} = c^2 \\nabla^2 u = c^2 \\left(\\frac{\\partial^2 u}{\\partial x^2} + \\frac{\\partial^2 u}{\\partial y^2} + \\frac{\\partial^2 u}{\\partial z^2}\\right)$$`,
      sender: 'assistant',
      timestamp: new Date(),
    },
    {
      id: '5',
      content: `流式输出测试 - 这段文本包含数学公式：

当我们讨论 $E = mc^2$ 时，我们在谈论质能等价关系。

$$\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$

这个积分在概率论中非常重要，特别是在正态分布的计算中。

**粗体文本** 和 *斜体文本* 应该正确渲染。

- 列表项 1: $\\alpha + \\beta = \\gamma$
- 列表项 2: $\\sin^2(x) + \\cos^2(x) = 1$

复杂公式测试：
$$\\sum_{n=0}^{\\infty} \\frac{x^n}{n!} = e^x$$`,
      sender: 'assistant',
      timestamp: new Date(),
    },
    {
      id: '2',
      content: `这是块级数学公式测试：

$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$

$$\\sum_{n=1}^{\\infty} \\frac{1}{n^2} = \\frac{\\pi^2}{6}$$`,
      sender: 'assistant',
      timestamp: new Date(),
    },
    {
      id: '3',
      content: `复杂数学公式测试：

$$\\begin{pmatrix}
a & b \\\\
c & d
\\end{pmatrix}
\\begin{pmatrix}
x \\\\
y
\\end{pmatrix}
=
\\begin{pmatrix}
ax + by \\\\
cx + dy
\\end{pmatrix}$$

$$f(x) = \\begin{cases}
x^2 & \\text{if } x \\geq 0 \\\\
-x^2 & \\text{if } x < 0
\\end{cases}$$`,
      sender: 'assistant',
      timestamp: new Date(),
    },
    {
      id: '4',
      content: `Markdown格式测试：

**粗体文本** 和 *斜体文本*

- 列表项1
- 列表项2 with math: $\\alpha + \\beta = \\gamma$
- 列表项3

1. 有序列表1
2. 有序列表2 with formula: $\\frac{a}{b} = c$

\`行内代码\` 和数学公式 $\\sin(\\theta) = \\cos(\\frac{\\pi}{2} - \\theta)$`,
      sender: 'assistant',
      timestamp: new Date(),
    },
  ]);

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>数学公式渲染测试页面</h1>
      <div style={{ marginBottom: '20px' }}>
        <p>这个页面用于测试LaTeX数学公式和Markdown格式的渲染效果。</p>
      </div>
      
      {testMessages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}
    </div>
  );
};

export default MathTestPage;