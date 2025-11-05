import React, { useEffect, useMemo, useRef, useState } from 'react';
import './OtherTools.css';
import JSZip from 'jszip';
import jsQR from 'jsqr';
import { PDFDocument } from 'pdf-lib';
import QRCode from 'qrcode';
import { marked } from 'marked';
import TurndownService from 'turndown';

/**
 * 其他功能页面入口组件
 * 说明：该页面提供若干通用实用工具，包含：
 * 1）JSON 格式化/校验；2）时间戳与日期互转；3）图片压缩；4）文件 SHA-256 哈希
 * 设计目标：不硬编码写死内容，均基于用户输入/上传进行实际功能处理
 */
const OtherTools: React.FC = () => {
  /**
   * 工具键类型：包含现有与新增工具
   */
  type ToolKey =
    | 'json'
    | 'timestamp'
    | 'image'
    | 'hash'
    | 'base64'
    | 'url'
    | 'mdhtml'
    | 'imgconvert'
    | 'qrcode'
    | 'zip'
    | 'pdf'
    | 'video';

  type Category = '全部' | '媒体处理' | 'PDF 文档' | '文件处理' | '文本与编码' | '转换与计算';

  /**
   * 工具注册表：集中管理标签、描述、分类与渲染组件
   */
  const tools: { key: ToolKey; label: string; desc: string; category: Category; render: () => JSX.Element; keywords?: string }[] = [
    { key: 'json', label: 'JSON 工具', desc: '格式化、校验与压缩 JSON 文本', category: '文本与编码', render: () => <JSONTool /> },
    { key: 'timestamp', label: '时间戳转换', desc: '秒/毫秒时间戳与日期互转', category: '转换与计算', render: () => <TimestampTool /> },
    { key: 'image', label: '图片压缩', desc: '浏览器端压缩图片并下载', category: '媒体处理', render: () => <ImageCompressorTool /> },
    { key: 'hash', label: '文件哈希', desc: '计算文件 SHA-256 哈希', category: '文件处理', render: () => <FileHashTool /> },
    { key: 'imgconvert', label: '图片格式转换', desc: 'PNG/JPG/WebP 互转', category: '媒体处理', render: () => <ImageFormatConverterTool /> },
    { key: 'qrcode', label: '二维码工具', desc: '生成与图片识别', category: '文本与编码', render: () => <QRCodeTool /> },
    { key: 'zip', label: 'ZIP 压缩/解压', desc: '打包多文件或解压预览', category: '文件处理', render: () => <ZipTool /> },
    { key: 'pdf', label: 'PDF 合并拆分', desc: 'pdf-lib 本地处理', category: 'PDF 文档', render: () => <PDFTools /> },
    { key: 'base64', label: 'Base64 编解码', desc: '文本/文件 base64', category: '文本与编码', render: () => <Base64Tool /> },
    { key: 'url', label: 'URL 编解码', desc: 'encode/decode', category: '文本与编码', render: () => <URLCodecTool /> },
    { key: 'mdhtml', label: 'Markdown ⇄ HTML', desc: '双向转换与预览', category: '文本与编码', render: () => <MarkdownHTMLTool /> },
    { key: 'video', label: '视频压缩(轻量)', desc: '浏览器实时转码', category: '媒体处理', render: () => <VideoCompressorLight /> },
  ];

  const categories: Category[] = ['全部', '媒体处理', 'PDF 文档', '文件处理', '文本与编码', '转换与计算'];

  const [active, setActive] = useState<ToolKey>('json');
  const [category, setCategory] = useState<Category>('全部');
  const [query, setQuery] = useState('');

  const filteredTools = useMemo(() => {
    return tools.filter((t) => {
      const inCat = category === '全部' || t.category === category;
      const inQuery = !query.trim()
        ? true
        : [t.label, t.desc, t.category, t.keywords || ''].join(' ').toLowerCase().includes(query.toLowerCase());
      return inCat && inQuery;
    });
  }, [category, query]);

  useEffect(() => {
    // 若当前激活工具不在筛选范围内，自动切换到第一个
    if (!filteredTools.some((t) => t.key === active) && filteredTools.length > 0) {
      setActive(filteredTools[0].key);
    }
  }, [filteredTools, active]);

  const activeTool = tools.find((t) => t.key === active) || filteredTools[0] || tools[0];

  return (
    <div className="other-tools-page">
      <div className="other-tools-header">
        <h1>其他功能</h1>
        <p>常用开发与学习生活辅助工具，全部在浏览器本地执行，无需上传服务器。</p>
      </div>

      <div className="other-tools-categories">
        {categories.map((c) => (
          <button
            key={c}
            className={`tab-btn ${category === c ? 'active' : ''}`}
            onClick={() => setCategory(c)}
            aria-pressed={category === c}
          >
            {c}
          </button>
        ))}
        <input
          className="tool-search"
          placeholder="搜索工具，例如：PDF、二维码..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <div className="other-tools-tabs">
        {filteredTools.map((t) => (
          <button
            key={t.key}
            className={`tab-btn ${active === t.key ? 'active' : ''}`}
            onClick={() => setActive(t.key)}
            aria-pressed={active === t.key}
            title={t.desc}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="tool-panel">
        {activeTool?.render()}
        {filteredTools.length === 0 && (
          <div className="status-text">未找到匹配工具，请更换分类或搜索关键词。</div>
        )}
      </div>
    </div>
  );
};

/**
 * JSON 工具组件
 * 功能：
 * - 校验 JSON 格式
 * - 美化/格式化（缩进）
 * - 压缩（移除空白）
 * - 复制输出与清空
 */
const JSONTool: React.FC = () => {
  const [input, setInput] = useState<string>('');
  const [output, setOutput] = useState<string>('');
  const [error, setError] = useState<string>('');

  /**
   * 尝试解析输入为 JSON
   * 返回：解析对象；若失败抛出异常
   */
  const parseJSON = (text: string): any => {
    return JSON.parse(text);
  };

  /**
   * 处理“格式化”动作：将合法 JSON 以 2 空格缩进美化输出
   */
  const handleFormat = () => {
    setError('');
    try {
      const obj = parseJSON(input);
      setOutput(JSON.stringify(obj, null, 2));
    } catch (e: any) {
      setError(`JSON 解析失败：${e?.message || e}`);
      setOutput('');
    }
  };

  /**
   * 处理“压缩”动作：移除所有空白压缩为一行
   */
  const handleMinify = () => {
    setError('');
    try {
      const obj = parseJSON(input);
      setOutput(JSON.stringify(obj));
    } catch (e: any) {
      setError(`JSON 解析失败：${e?.message || e}`);
      setOutput('');
    }
  };

  /**
   * 复制输出到剪贴板
   */
  const handleCopy = async () => {
    if (!output) return;
    try {
      await navigator.clipboard.writeText(output);
    } catch (e) {
      // 部分浏览器不支持，无需抛错
    }
  };

  /**
   * 清空输入与输出
   */
  const handleClear = () => {
    setInput('');
    setOutput('');
    setError('');
  };

  return (
    <div className="tool-card">
      <div className="tool-card-header">
        <h2>JSON 格式化与校验</h2>
        <p>在左侧输入 JSON，点击右上角按钮进行操作。</p>
      </div>

      <div className="json-grid">
        <div className="json-col">
          <label className="field-label">输入 JSON</label>
          <textarea
            className="json-textarea"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder='例如：{"name":"Alice","age":18,"tags":["a","b"]}'
          />
        </div>

        <div className="json-col">
          <div className="json-actions">
            <button onClick={handleFormat}>格式化</button>
            <button onClick={handleMinify}>压缩</button>
            <button onClick={handleCopy} disabled={!output}>
              复制输出
            </button>
            <button onClick={handleClear}>清空</button>
          </div>
          {error && <div className="error-text">{error}</div>}
          <label className="field-label">输出结果</label>
          <textarea
            className="json-textarea"
            value={output}
            onChange={(e) => setOutput(e.target.value)}
            placeholder="格式化或压缩后的结果将显示在此"
          />
        </div>
      </div>
    </div>
  );
};

/**
 * 时间戳转换工具组件
 * 功能：
 * - 秒/毫秒级时间戳 -> 本地时间字符串
 * - 日期字符串 -> 时间戳（毫秒）
 * - 支持使用当前时间进行演示
 */
const TimestampTool: React.FC = () => {
  const [tsInput, setTsInput] = useState<string>('');
  const [dateInput, setDateInput] = useState<string>('');
  const [tsToDate, setTsToDate] = useState<string>('');
  const [dateToTs, setDateToTs] = useState<string>('');

  /**
   * 判断并解析时间戳（自动识别秒/毫秒）
   */
  const parseTimestamp = (raw: string): number | null => {
    if (!raw) return null;
    const n = Number(raw.trim());
    if (!Number.isFinite(n)) return null;
    // 长度<=10 视为秒，否则视为毫秒
    const isSeconds = String(Math.floor(n)).length <= 10;
    return isSeconds ? n * 1000 : n;
  };

  /**
   * 将时间戳转换为本地时间字符串
   */
  const handleTsToDate = () => {
    const ms = parseTimestamp(tsInput);
    if (ms == null) {
      setTsToDate('无效的时间戳');
      return;
    }
    const d = new Date(ms);
    if (isNaN(d.getTime())) {
      setTsToDate('无效的时间戳');
      return;
    }
    setTsToDate(
      `${d.toLocaleString()}（本地时区，毫秒=${d.getTime()}）`
    );
  };

  /**
   * 将日期字符串转换为毫秒时间戳
   */
  const handleDateToTs = () => {
    if (!dateInput.trim()) {
      setDateToTs('请输入日期字符串，例如 2024-01-01 12:00:00');
      return;
    }
    const d = new Date(dateInput);
    const t = d.getTime();
    if (!Number.isFinite(t)) {
      setDateToTs('无法解析该日期字符串');
      return;
    }
    setDateToTs(`${t}（毫秒） / ${Math.floor(t / 1000)}（秒）`);
  };

  /**
   * 使用当前时间填充演示
   */
  const handleUseNow = () => {
    const now = Date.now();
    setTsInput(String(now));
    setDateInput(new Date(now).toLocaleString());
    setTsToDate('');
    setDateToTs('');
  };

  return (
    <div className="tool-card">
      <div className="tool-card-header">
        <h2>时间戳与日期互转</h2>
        <p>自动识别秒/毫秒时间戳，结果基于当前浏览器本地时区。</p>
      </div>

      <div className="ts-grid">
        <div className="ts-col">
          <label className="field-label">时间戳（秒或毫秒）</label>
          <input
            className="text-input"
            value={tsInput}
            onChange={(e) => setTsInput(e.target.value)}
            placeholder="例如 1704067200 或 1704067200000"
          />
          <button onClick={handleTsToDate}>时间戳 → 日期</button>
          <div className="result-box">{tsToDate || '结果将显示在此'}</div>
        </div>

        <div className="ts-col">
          <label className="field-label">日期字符串</label>
          <input
            className="text-input"
            value={dateInput}
            onChange={(e) => setDateInput(e.target.value)}
            placeholder="例如 2024-01-01 12:00:00"
          />
          <button onClick={handleDateToTs}>日期 → 时间戳</button>
          <div className="result-box">{dateToTs || '结果将显示在此'}</div>
        </div>
      </div>

      <div className="ts-actions">
        <button onClick={handleUseNow}>使用当前时间</button>
      </div>
    </div>
  );
};

/**
 * 图片压缩工具组件
 * 功能：
 * - 前端读取图片文件，使用 Canvas 按设定质量与最大宽度进行压缩
 * - 显示原图与压缩图大小、预览，并支持下载压缩后的图片
 */
const ImageCompressorTool: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [originalURL, setOriginalURL] = useState<string>('');
  const [compressedBlob, setCompressedBlob] = useState<Blob | null>(null);
  const [compressedURL, setCompressedURL] = useState<string>('');
  const [quality, setQuality] = useState<number>(0.7);
  const [maxWidth, setMaxWidth] = useState<number>(1280);
  const [status, setStatus] = useState<string>('');

  useEffect(() => {
    return () => {
      if (originalURL) URL.revokeObjectURL(originalURL);
      if (compressedURL) URL.revokeObjectURL(compressedURL);
    };
  }, [originalURL, compressedURL]);

  /**
   * 选择文件时更新本地预览 URL
   */
  const handleFileChange: React.ChangeEventHandler<HTMLInputElement> = (e) => {
    const f = e.target.files?.[0] || null;
    setFile(f);
    setCompressedBlob(null);
    setCompressedURL('');
    if (originalURL) URL.revokeObjectURL(originalURL);
    if (f) {
      const url = URL.createObjectURL(f);
      setOriginalURL(url);
    } else {
      setOriginalURL('');
    }
    setStatus('');
  };

  /**
   * 使用 Canvas 压缩图像，输出 JPEG Blob
   */
  const compress = async () => {
    if (!file) return;
    setStatus('压缩中...');
    try {
      const img = await readImageFromFile(file);
      const { canvas, scale } = drawToCanvas(img, maxWidth);
      const blob = await canvasToBlob(canvas, 'image/jpeg', quality);
      if (!blob) throw new Error('压缩失败，未获得 Blob');

      if (compressedURL) URL.revokeObjectURL(compressedURL);
      const url = URL.createObjectURL(blob);
      setCompressedBlob(blob);
      setCompressedURL(url);
      setStatus(`压缩完成（缩放比例 ${Math.round(scale * 100)}%，质量 ${quality}）`);
    } catch (e: any) {
      setStatus(`压缩失败：${e?.message || e}`);
    }
  };

  /**
   * 下载压缩后的图片
   */
  const handleDownload = () => {
    if (!compressedBlob) return;
    const a = document.createElement('a');
    const url = compressedURL || URL.createObjectURL(compressedBlob);
    a.href = url;
    a.download = makeDownloadName(file, 'compressed');
    a.click();
  };

  return (
    <div className="tool-card">
      <div className="tool-card-header">
        <h2>图片压缩</h2>
        <p>仅在本地浏览器处理，不会上传服务器。支持设置质量与最大宽度。</p>
      </div>

      <div className="img-actions">
        <input type="file" accept="image/*" onChange={handleFileChange} />

        <div className="inline-group">
          <label>质量：{quality.toFixed(2)}</label>
          <input
            type="range"
            min={0.1}
            max={1}
            step={0.05}
            value={quality}
            onChange={(e) => setQuality(Number(e.target.value))}
          />
        </div>

        <div className="inline-group">
          <label>最大宽度：{maxWidth}px</label>
          <input
            type="range"
            min={320}
            max={4096}
            step={10}
            value={maxWidth}
            onChange={(e) => setMaxWidth(Number(e.target.value))}
          />
        </div>

        <button onClick={compress} disabled={!file}>开始压缩</button>
        <button onClick={handleDownload} disabled={!compressedBlob}>下载压缩图片</button>
      </div>

      {status && <div className="status-text">{status}</div>}

      <div className="img-preview-grid">
        <div className="img-box">
          <div className="img-label">原图{file ? `（${prettySize(file.size)}）` : ''}</div>
          {originalURL ? (
            <img src={originalURL} alt="original" />
          ) : (
            <div className="placeholder">请选择一张图片</div>
          )}
        </div>

        <div className="img-box">
          <div className="img-label">
            压缩后
            {compressedBlob ? `（${prettySize(compressedBlob.size)}）` : ''}
          </div>
          {compressedURL ? (
            <img src={compressedURL} alt="compressed" />
          ) : (
            <div className="placeholder">压缩结果预览</div>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * 文件哈希工具组件
 * 功能：
 * - 选择任意文件，使用 Web Crypto 计算 SHA-256 哈希
 * - 显示十六进制哈希值并支持复制
 */
const FileHashTool: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [hash, setHash] = useState<string>('');
  const [status, setStatus] = useState<string>('');

  /**
   * 选择文件
   */
  const handleFile: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
    const f = e.target.files?.[0] || null;
    setFile(f);
    setHash('');
    setStatus('');
  };

  /**
   * 计算 SHA-256 哈希
   */
  const handleCalc = async () => {
    if (!file) return;
    setStatus('计算中...');
    try {
      const buf = await file.arrayBuffer();
      const digest = await crypto.subtle.digest('SHA-256', buf);
      const hex = bufferToHex(digest);
      setHash(hex);
      setStatus('计算完成');
    } catch (e: any) {
      setStatus(`计算失败：${e?.message || e}`);
    }
  };

  /**
   * 复制哈希
   */
  const handleCopy = async () => {
    if (!hash) return;
    try {
      await navigator.clipboard.writeText(hash);
    } catch {}
  };

  return (
    <div className="tool-card">
      <div className="tool-card-header">
        <h2>文件 SHA-256 哈希</h2>
        <p>用于校验文件一致性或分发校验值。</p>
      </div>

      <div className="hash-actions">
        <input type="file" onChange={handleFile} />
        <button onClick={handleCalc} disabled={!file}>计算哈希</button>
      </div>
      {status && <div className="status-text">{status}</div>}
      <div className="result-box mono">{hash || '哈希结果将显示在此'}</div>
      <div className="hash-actions">
        <button onClick={handleCopy} disabled={!hash}>复制哈希</button>
      </div>
    </div>
  );
};

/**
 * 工具函数：将 ArrayBuffer 转为十六进制字符串
 */
function bufferToHex(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  const hex: string[] = [];
  for (let i = 0; i < bytes.length; i++) {
    const h = bytes[i].toString(16).padStart(2, '0');
    hex.push(h);
  }
  return hex.join('');
}

/**
 * 工具函数：从文件读取 Image 对象
 */
function readImageFromFile(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = (e) => reject(new Error('图片加载失败'));
    img.src = url;
  });
}

/**
 * 工具函数：将图片绘制到 Canvas，并按最大宽度缩放
 */
function drawToCanvas(img: HTMLImageElement, maxWidth: number): { canvas: HTMLCanvasElement; scale: number } {
  const scale = img.width > maxWidth ? maxWidth / img.width : 1;
  const w = Math.round(img.width * scale);
  const h = Math.round(img.height * scale);
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Canvas 不可用');
  ctx.drawImage(img, 0, 0, w, h);
  return { canvas, scale };
}

/**
 * 工具函数：Canvas 转 Blob
 */
function canvasToBlob(canvas: HTMLCanvasElement, type: string, quality: number): Promise<Blob | null> {
  return new Promise((resolve) => canvas.toBlob(resolve, type, quality));
}

/**
 * 工具函数：生成下载文件名
 */
function makeDownloadName(file: File | null, suffix: string): string {
  if (!file) return `image_${suffix}.jpg`;
  const base = file.name.replace(/\.[^.]+$/, '');
  return `${base}_${suffix}.jpg`;
}

/**
 * 工具函数：字节大小友好显示
 */
function prettySize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

/**
 * Base64 编解码工具组件
 * 功能：
 * - 文本 → Base64 与 Base64 → 文本
 * - 文件 → Base64 与 Base64 → 文件（下载）
 */
const Base64Tool: React.FC = () => {
  const [text, setText] = useState('');
  const [b64, setB64] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState('');

  const encodeText = () => {
    try {
      setB64(btoa(unescape(encodeURIComponent(text))));
      setStatus('文本已编码');
    } catch (e: any) {
      setStatus(`编码失败：${e?.message || e}`);
    }
  };

  const decodeText = () => {
    try {
      setText(decodeURIComponent(escape(atob(b64))));
      setStatus('文本已解码');
    } catch (e: any) {
      setStatus(`解码失败：${e?.message || e}`);
    }
  };

  const handleFile: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
    const f = e.target.files?.[0] || null;
    setFile(f);
  };

  const encodeFile = async () => {
    if (!file) return;
    setStatus('文件编码中...');
    const buf = await file.arrayBuffer();
    const bytes = new Uint8Array(buf);
    let binary = '';
    for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
    setB64(btoa(binary));
    setStatus(`文件编码完成，长度 ${b64.length}`);
  };

  const decodeFile = () => {
    try {
      const binary = atob(b64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      const blob = new Blob([bytes.buffer]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'decoded.bin';
      a.click();
      URL.revokeObjectURL(url);
      setStatus('已从 Base64 生成文件并下载');
    } catch (e: any) {
      setStatus(`Base64 转文件失败：${e?.message || e}`);
    }
  };

  return (
    <div className="tool-card">
      <div className="tool-card-header">
        <h2>Base64 编解码</h2>
        <p>支持文本与文件的 Base64 编解码。</p>
      </div>

      <div className="json-grid">
        <div className="json-col">
          <label className="field-label">文本</label>
          <textarea className="json-textarea" value={text} onChange={(e) => setText(e.target.value)} />
          <div className="json-actions">
            <button onClick={encodeText}>文本 → Base64</button>
            <button onClick={decodeText}>Base64 → 文本</button>
          </div>
        </div>
        <div className="json-col">
          <label className="field-label">Base64</label>
          <textarea className="json-textarea" value={b64} onChange={(e) => setB64(e.target.value)} />
          <div className="json-actions">
            <input type="file" onChange={handleFile} />
            <button onClick={encodeFile} disabled={!file}>文件 → Base64</button>
            <button onClick={decodeFile} disabled={!b64}>Base64 → 文件</button>
          </div>
        </div>
      </div>
      {status && <div className="status-text">{status}</div>}
    </div>
  );
};

/**
 * URL 编解码工具组件
 * 功能：encodeURIComponent / decodeURIComponent
 */
const URLCodecTool: React.FC = () => {
  const [raw, setRaw] = useState('');
  const [encoded, setEncoded] = useState('');

  const doEncode = () => setEncoded(encodeURIComponent(raw));
  const doDecode = () => setRaw(decodeURIComponent(encoded));

  return (
    <div className="tool-card">
      <div className="tool-card-header">
        <h2>URL 编解码</h2>
        <p>对 URL 参数等进行安全转义与还原。</p>
      </div>
      <div className="json-grid">
        <div className="json-col">
          <label className="field-label">原始文本</label>
          <textarea className="json-textarea" value={raw} onChange={(e) => setRaw(e.target.value)} />
          <button onClick={doEncode}>编码 →</button>
        </div>
        <div className="json-col">
          <label className="field-label">已编码</label>
          <textarea className="json-textarea" value={encoded} onChange={(e) => setEncoded(e.target.value)} />
          <button onClick={doDecode}>← 解码</button>
        </div>
      </div>
    </div>
  );
};

/**
 * Markdown ⇄ HTML 转换工具
 * 功能：
 * - 使用 marked 将 Markdown 转 HTML 字符串并预览
 * - 使用 Turndown 将 HTML 转 Markdown
 */
const MarkdownHTMLTool: React.FC = () => {
  const [md, setMd] = useState<string>('# 标题\n\n这是一个示例。');
  const [html, setHtml] = useState<string>('');
  const [status, setStatus] = useState('');
  const td = useMemo(() => new TurndownService(), []);

  useEffect(() => {
    setHtml(marked.parse(md) as string);
  }, [md]);

  const htmlToMd = () => {
    try {
      const out = td.turndown(html);
      setMd(out);
      setStatus('已将 HTML 转为 Markdown');
    } catch (e: any) {
      setStatus(`转换失败：${e?.message || e}`);
    }
  };

  return (
    <div className="tool-card">
      <div className="tool-card-header">
        <h2>Markdown ⇄ HTML</h2>
        <p>支持双向转换，右侧显示 HTML 渲染效果。</p>
      </div>
      <div className="json-grid">
        <div className="json-col">
          <label className="field-label">Markdown</label>
          <textarea className="json-textarea" value={md} onChange={(e) => setMd(e.target.value)} />
          <div className="json-actions">
            <button onClick={() => setHtml(marked.parse(md) as string)}>Markdown → HTML</button>
          </div>
        </div>
        <div className="json-col">
          <label className="field-label">HTML</label>
          <textarea className="json-textarea" value={html} onChange={(e) => setHtml(e.target.value)} />
          <div className="json-actions">
            <button onClick={htmlToMd}>HTML → Markdown</button>
          </div>
          <label className="field-label">HTML 预览</label>
          <div className="result-box" dangerouslySetInnerHTML={{ __html: html }} />
        </div>
      </div>
      {status && <div className="status-text">{status}</div>}
    </div>
  );
};

/**
 * 图片格式转换工具组件
 * 功能：
 * - 选择图片并转换为 PNG/JPG/WebP
 * - 可设置 JPG/WebP 质量
 */
const ImageFormatConverterTool: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [srcURL, setSrcURL] = useState('');
  const [fmt, setFmt] = useState<'image/png' | 'image/jpeg' | 'image/webp'>('image/webp');
  const [quality, setQuality] = useState(0.8);
  const [outURL, setOutURL] = useState('');
  const [status, setStatus] = useState('');

  useEffect(() => () => {
    if (srcURL) URL.revokeObjectURL(srcURL);
    if (outURL) URL.revokeObjectURL(outURL);
  }, [srcURL, outURL]);

  const onFile: React.ChangeEventHandler<HTMLInputElement> = (e) => {
    const f = e.target.files?.[0] || null;
    setFile(f);
    if (srcURL) URL.revokeObjectURL(srcURL);
    if (f) setSrcURL(URL.createObjectURL(f));
  };

  const convert = async () => {
    if (!file) return;
    setStatus('转换中...');
    try {
      const img = await readImageFromFile(file);
      const { canvas } = drawToCanvas(img, img.width);
      const blob = await canvasToBlob(canvas, fmt, fmt === 'image/png' ? 1 : quality);
      if (!blob) throw new Error('未生成输出');
      if (outURL) URL.revokeObjectURL(outURL);
      const url = URL.createObjectURL(blob);
      setOutURL(url);
      setStatus('转换完成');
    } catch (e: any) {
      setStatus(`转换失败：${e?.message || e}`);
    }
  };

  const download = () => {
    if (!outURL) return;
    const a = document.createElement('a');
    a.href = outURL;
    const ext = fmt === 'image/png' ? 'png' : fmt === 'image/jpeg' ? 'jpg' : 'webp';
    a.download = makeDownloadName(file, `converted.${ext}`);
    a.click();
  };

  return (
    <div className="tool-card">
      <div className="tool-card-header">
        <h2>图片格式转换</h2>
        <p>支持 PNG / JPG / WebP 互转。</p>
      </div>
      <div className="img-actions">
        <input type="file" accept="image/*" onChange={onFile} />
        <div className="inline-group">
          <label>目标格式：</label>
          <select value={fmt} onChange={(e) => setFmt(e.target.value as any)}>
            <option value="image/webp">WebP</option>
            <option value="image/jpeg">JPG</option>
            <option value="image/png">PNG</option>
          </select>
        </div>
        {(fmt === 'image/jpeg' || fmt === 'image/webp') && (
          <div className="inline-group">
            <label>质量：{quality.toFixed(2)}</label>
            <input type="range" min={0.1} max={1} step={0.05} value={quality} onChange={(e) => setQuality(Number(e.target.value))} />
          </div>
        )}
        <button onClick={convert} disabled={!file}>开始转换</button>
        <button onClick={download} disabled={!outURL}>下载结果</button>
      </div>
      {status && <div className="status-text">{status}</div>}
      <div className="img-preview-grid">
        <div className="img-box">
          <div className="img-label">原图</div>
          {srcURL ? <img src={srcURL} /> : <div className="placeholder">请选择图片</div>}
        </div>
        <div className="img-box">
          <div className="img-label">输出</div>
          {outURL ? <img src={outURL} /> : <div className="placeholder">转换结果预览</div>}
        </div>
      </div>
    </div>
  );
};

/**
 * 二维码工具组件
 * 功能：
 * - 文本生成二维码（PNG）
 * - 从图片识别二维码内容
 */
const QRCodeTool: React.FC = () => {
  const [text, setText] = useState('中国海洋大学 WePlus 校园助手');
  const [qrUrl, setQrUrl] = useState('');
  const [status, setStatus] = useState('');
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const gen = async () => {
    try {
      const url = await QRCode.toDataURL(text, { errorCorrectionLevel: 'M', margin: 2, width: 256 });
      setQrUrl(url);
      setStatus('已生成二维码');
    } catch (e: any) {
      setStatus(`生成失败：${e?.message || e}`);
    }
  };

  const onPickImg: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const cvs = canvasRef.current || document.createElement('canvas');
      canvasRef.current = cvs;
      cvs.width = img.width;
      cvs.height = img.height;
      const ctx = cvs.getContext('2d');
      if (!ctx) return;
      ctx.drawImage(img, 0, 0);
      const imageData = ctx.getImageData(0, 0, cvs.width, cvs.height);
      const code = jsQR(imageData.data, cvs.width, cvs.height);
      if (code?.data) {
        setText(code.data);
        setStatus('识别成功，内容已填入文本框');
      } else {
        setStatus('未识别到二维码');
      }
      URL.revokeObjectURL(url);
    };
    img.onerror = () => {
      setStatus('图片加载失败');
      URL.revokeObjectURL(url);
    };
    img.src = url;
  };

  const download = () => {
    if (!qrUrl) return;
    const a = document.createElement('a');
    a.href = qrUrl;
    a.download = 'qrcode.png';
    a.click();
  };

  return (
    <div className="tool-card">
      <div className="tool-card-header">
        <h2>二维码生成与识别</h2>
        <p>本地生成 PNG 二维码，或从图片识别二维码。</p>
      </div>
      <div className="img-actions">
        <input className="text-input" value={text} onChange={(e) => setText(e.target.value)} placeholder="输入文本..." />
        <button onClick={gen}>生成二维码</button>
        <button onClick={download} disabled={!qrUrl}>下载二维码</button>
        <input type="file" accept="image/*" onChange={onPickImg} />
      </div>
      {status && <div className="status-text">{status}</div>}
      <div className="img-preview-grid">
        <div className="img-box">
          <div className="img-label">二维码预览</div>
          {qrUrl ? <img src={qrUrl} /> : <div className="placeholder">点击“生成二维码”查看</div>}
        </div>
      </div>
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  );
};

/**
 * ZIP 压缩/解压工具组件
 * 功能：
 * - 多文件压缩为 zip 并下载
 * - 选择 zip 文件解压，列出内容并单个下载
 */
const ZipTool: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [zipStatus, setZipStatus] = useState('');
  const [entries, setEntries] = useState<{ name: string; blobUrl: string; size: number }[]>([]);

  const onPickFiles: React.ChangeEventHandler<HTMLInputElement> = (e) => {
    const list = e.target.files ? Array.from(e.target.files) : [];
    setFiles(list);
  };

  const compress = async () => {
    if (!files.length) return;
    setZipStatus('压缩中...');
    const zip = new JSZip();
    files.forEach((f) => zip.file(f.name, f));
    const blob = await zip.generateAsync({ type: 'blob' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'archive.zip';
    a.click();
    URL.revokeObjectURL(url);
    setZipStatus('压缩完成并下载');
  };

  const onPickZip: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
    const zipFile = e.target.files?.[0];
    if (!zipFile) return;
    setZipStatus('解压中...');
    const buf = await zipFile.arrayBuffer();
    const zip = await JSZip.loadAsync(buf);
    const out: { name: string; blobUrl: string; size: number }[] = [];
    for (const [path, entry] of Object.entries(zip.files)) {
      if (entry.dir) continue;
      const blob = await entry.async('blob');
      out.push({ name: path, blobUrl: URL.createObjectURL(blob), size: blob.size });
    }
    setEntries(out);
    setZipStatus(`解压完成，共 ${out.length} 个文件`);
  };

  return (
    <div className="tool-card">
      <div className="tool-card-header">
        <h2>ZIP 压缩与解压</h2>
        <p>将多文件打包为 ZIP，或解压 ZIP 以逐个下载。</p>
      </div>
      <div className="img-actions">
        <input type="file" multiple onChange={onPickFiles} />
        <button onClick={compress} disabled={!files.length}>压缩所选文件</button>
        <span className="placeholder">或</span>
        <input type="file" accept=".zip" onChange={onPickZip} />
      </div>
      {zipStatus && <div className="status-text">{zipStatus}</div>}
      {entries.length > 0 && (
        <div className="img-box" style={{ marginTop: 12 }}>
          <div className="img-label">解压结果</div>
          <ul>
            {entries.map((e, i) => (
              <li key={i} style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
                <span style={{ flex: 1 }}>{e.name}（{prettySize(e.size)}）</span>
                <a href={e.blobUrl} download>下载</a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

/**
 * PDF 工具组件
 * 功能：
 * - 合并多个 PDF
 * - 拆分 PDF 指定页码（如 1-3,5）
 */
const PDFTools: React.FC = () => {
  const [mergeFiles, setMergeFiles] = useState<File[]>([]);
  const [splitFile, setSplitFile] = useState<File | null>(null);
  const [range, setRange] = useState('1-');
  const [status, setStatus] = useState('');

  const onMergePick: React.ChangeEventHandler<HTMLInputElement> = (e) => {
    setMergeFiles(e.target.files ? Array.from(e.target.files) : []);
  };
  const onSplitPick: React.ChangeEventHandler<HTMLInputElement> = (e) => {
    setSplitFile(e.target.files?.[0] || null);
  };

  const doMerge = async () => {
    if (!mergeFiles.length) return;
    setStatus('合并中...');
    const out = await PDFDocument.create();
    for (const f of mergeFiles) {
      const buf = await f.arrayBuffer();
      const doc = await PDFDocument.load(buf);
      const pages = await out.copyPages(doc, doc.getPageIndices());
      pages.forEach((p) => out.addPage(p));
    }
    const pdfBytes = await out.save();
    const url = URL.createObjectURL(new Blob([pdfBytes], { type: 'application/pdf' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'merged.pdf';
    a.click();
    URL.revokeObjectURL(url);
    setStatus('合并完成并下载');
  };

  const parseRanges = (txt: string, total: number): number[] => {
    const parts = txt.split(/[,，]/).map((s) => s.trim()).filter(Boolean);
    const pages = new Set<number>();
    for (const p of parts) {
      if (/^\d+$/.test(p)) {
        const n = Number(p) - 1;
        if (n >= 0 && n < total) pages.add(n);
      } else {
        const m = p.match(/^(\d*)-(\d*)$/);
        if (m) {
          const start = m[1] ? Number(m[1]) - 1 : 0;
          const end = m[2] ? Number(m[2]) - 1 : total - 1;
          for (let i = Math.max(0, start); i <= Math.min(total - 1, end); i++) pages.add(i);
        }
      }
    }
    return Array.from(pages).sort((a, b) => a - b);
  };

  const doSplit = async () => {
    if (!splitFile) return;
    setStatus('拆分中...');
    const buf = await splitFile.arrayBuffer();
    const doc = await PDFDocument.load(buf);
    const total = doc.getPageCount();
    const pages = parseRanges(range, total);
    if (!pages.length) {
      setStatus('页码范围无效');
      return;
    }
    const out = await PDFDocument.create();
    const copied = await out.copyPages(doc, pages);
    copied.forEach((p) => out.addPage(p));
    const bytes = await out.save();
    const url = URL.createObjectURL(new Blob([bytes], { type: 'application/pdf' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'split.pdf';
    a.click();
    URL.revokeObjectURL(url);
    setStatus('拆分完成并下载');
  };

  return (
    <div className="tool-card">
      <div className="tool-card-header">
        <h2>PDF 合并与拆分</h2>
        <p>完全在浏览器端进行，无需上传。</p>
      </div>
      <div className="img-actions">
        <div className="inline-group">
          <label>选择多个 PDF 合并：</label>
          <input type="file" accept="application/pdf" multiple onChange={onMergePick} />
          <button onClick={doMerge} disabled={!mergeFiles.length}>合并下载</button>
        </div>
      </div>
      <div className="img-actions">
        <div className="inline-group">
          <label>选择单个 PDF 拆分：</label>
          <input type="file" accept="application/pdf" onChange={onSplitPick} />
          <input className="text-input" placeholder="页码范围，如 1-3,5" value={range} onChange={(e) => setRange(e.target.value)} />
          <button onClick={doSplit} disabled={!splitFile}>拆分下载</button>
        </div>
      </div>
      {status && <div className="status-text">{status}</div>}
    </div>
  );
};

/**
 * 轻量视频压缩工具（MediaRecorder 实时转码）
 * 功能：
 * - 将本地视频播放到 Canvas，并用 MediaRecorder 以指定宽度与比特率录制为 webm
 * 说明：实时处理，视频越长耗时越久；兼容度高、无需加载 wasm。
 */
const VideoCompressorLight: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState('');
  const [targetWidth, setTargetWidth] = useState(960);
  const [bitrate, setBitrate] = useState(1200_000); // 1.2Mbps
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [outURL, setOutURL] = useState('');

  useEffect(() => () => {
    if (outURL) URL.revokeObjectURL(outURL);
  }, [outURL]);

  const onPick: React.ChangeEventHandler<HTMLInputElement> = (e) => {
    const f = e.target.files?.[0] || null;
    setFile(f);
    setStatus('');
  };

  const startCompress = async () => {
    if (!file) return;
    setStatus('初始化中...');
    const video = document.createElement('video');
    videoRef.current = video;
    video.src = URL.createObjectURL(file);
    await video.play().catch(() => {});
    await new Promise((r) => (video.onloadedmetadata = () => r(null)));

    const scale = Math.min(1, targetWidth / video.videoWidth);
    const w = Math.round(video.videoWidth * scale);
    const h = Math.round(video.videoHeight * scale);
    const canvas = document.createElement('canvas');
    canvasRef.current = canvas;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      setStatus('Canvas 不可用');
      return;
    }

    const stream = (canvas as any).captureStream ? (canvas as any).captureStream(30) : null;
    if (!stream) {
      setStatus('浏览器不支持 captureStream');
      return;
    }
    const rec = new MediaRecorder(stream as MediaStream, {
      mimeType: 'video/webm;codecs=vp8',
      videoBitsPerSecond: bitrate,
    });

    const chunks: Blob[] = [];
    rec.ondataavailable = (e) => e.data && chunks.push(e.data);
    rec.onstop = () => {
      const blob = new Blob(chunks, { type: 'video/webm' });
      const url = URL.createObjectURL(blob);
      setOutURL(url);
      setStatus('压缩完成，可下载');
      URL.revokeObjectURL(video.src);
    };

    setStatus('压缩中（实时转码）...');
    rec.start();

    const render = () => {
      ctx.drawImage(video, 0, 0, w, h);
      if (!video.paused && !video.ended) requestAnimationFrame(render);
    };
    requestAnimationFrame(render);

    await video.play();
    await new Promise((r) => (video.onended = () => r(null)));
    rec.stop();
  };

  const download = () => {
    if (!outURL) return;
    const a = document.createElement('a');
    a.href = outURL;
    a.download = 'compressed.webm';
    a.click();
  };

  return (
    <div className="tool-card">
      <div className="tool-card-header">
        <h2>视频压缩（轻量）</h2>
        <p>无需 wasm，实时转码为 WebM，适合快速减小体积（浏览器支持）。</p>
      </div>
      <div className="img-actions">
        <input type="file" accept="video/*" onChange={onPick} />
        <div className="inline-group">
          <label>目标宽度：{targetWidth}px</label>
          <input type="range" min={320} max={1920} step={10} value={targetWidth} onChange={(e) => setTargetWidth(Number(e.target.value))} />
        </div>
        <div className="inline-group">
          <label>码率：{(bitrate / 1000).toFixed(0)} kbps</label>
          <input type="range" min={300_000} max={3_000_000} step={50_000} value={bitrate} onChange={(e) => setBitrate(Number(e.target.value))} />
        </div>
        <button onClick={startCompress} disabled={!file}>开始压缩</button>
        <button onClick={download} disabled={!outURL}>下载结果</button>
      </div>
      {status && <div className="status-text">{status}</div>}
    </div>
  );
};

export default OtherTools;
