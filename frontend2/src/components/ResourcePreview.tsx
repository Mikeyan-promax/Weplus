import React, { useState, useEffect } from 'react';
import './ResourcePreview.css';

interface ResourcePreviewProps {
  resourceId: number;
  fileName: string;
  fileType: string;
  fileSize: number;
  onClose: () => void;
}

/**
 * 资源预览组件
 * 负责调用后端预览接口获取 Blob，并根据实际 MIME 类型渲染对应的预览内容。
 * 注意：后端存储的 file_type 多为扩展名（如 'pdf'、'png'），
 *       本组件统一以响应的 Blob.type（MIME）为准进行渲染，
 *       同时提供扩展名到 MIME 的映射作为回退，以兼容旧数据。
 */
const ResourcePreview: React.FC<ResourcePreviewProps> = ({
  resourceId,
  fileName,
  fileType,
  fileSize,
  onClose
}) => {
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [mimeType, setMimeType] = useState<string>('');

  useEffect(() => {
    /**
     * 加载预览内容
     * 调用后端 /preview 接口获取文件 Blob，并记录其 MIME 类型用于后续渲染。
     */
    const loadPreview = async () => {
      try {
        setLoading(true);
        setError('');
        
        // 获取文件预览URL
        const response = await fetch(`http://localhost:8000/api/study-resources/${resourceId}/preview`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to load preview');
        }

        const blob = await response.blob();
        // 记录后端返回的真实 MIME 类型（更可靠）
        setMimeType(blob.type || '');
        const url = URL.createObjectURL(blob);
        setPreviewUrl(url);
      } catch (err) {
        setError('预览加载失败');
        console.error('Preview load error:', err);
      } finally {
        setLoading(false);
      }
    };

    loadPreview();

    // 清理URL对象
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [resourceId]);

  /**
   * 格式化文件大小显示
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  /**
   * 扩展名到 MIME 的简单映射（用于旧数据的回退）
   */
  const extToMime: Record<string, string> = {
    pdf: 'application/pdf',
    txt: 'text/plain',
    md: 'text/markdown',
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
    png: 'image/png',
    gif: 'image/gif',
    mp4: 'video/mp4',
    mp3: 'audio/mpeg',
    wav: 'audio/wav',
    doc: 'application/msword',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ppt: 'application/vnd.ms-powerpoint',
    pptx: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    xls: 'application/vnd.ms-excel',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  };

  /**
   * 从文件名或 fileType 推断扩展名，再映射为 MIME
   */
  const inferMimeFromExt = (nameOrExt: string): string | undefined => {
    if (!nameOrExt) return undefined;
    const lower = nameOrExt.toLowerCase();
    // 如果是完整文件名，从最后一个点取扩展名
    const ext = lower.includes('.') ? lower.split('.').pop() : lower;
    return ext ? extToMime[ext] : undefined;
  };

  /**
   * 统一得到有效的 MIME 类型（优先使用后端 Blob.type；其次用扩展名映射）
   */
  const getEffectiveMime = (): string => {
    if (mimeType && typeof mimeType === 'string' && mimeType.length > 0) return mimeType;
    const byExt = inferMimeFromExt(fileType) || inferMimeFromExt(fileName);
    return byExt || 'application/octet-stream';
  };

  /**
   * 根据 MIME 类型返回文件图标
   */
  const getFileIcon = (type: string): string => {
    const t = type.toLowerCase();
    if (t.startsWith('image/')) return '🖼️';
    if (t === 'application/pdf') return '📄';
    if (t.startsWith('video/')) return '🎬';
    if (t.startsWith('audio/')) return '🎵';
    if (t.includes('word')) return '📝';
    if (t.includes('excel') || t.includes('spreadsheet')) return '📊';
    if (t.includes('powerpoint') || t.includes('presentation')) return '📽️';
    if (t.startsWith('text/')) return '📃';
    return '📁';
  };

  const renderPreview = () => {
    if (loading) {
      return (
        <div className="preview-loading">
          <div className="loading-spinner"></div>
          <p>正在加载预览...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="preview-error">
          <div className="error-icon">⚠️</div>
          <p>{error}</p>
          <button onClick={() => window.open(`http://localhost:8000/api/study-resources/${resourceId}/download`, '_blank')}>
            下载文件
          </button>
        </div>
      );
    }

    const effectiveMime = getEffectiveMime();

    // 图片预览
    if (effectiveMime.startsWith('image/')) {
      return (
        <div className="preview-image">
          <img src={previewUrl} alt={fileName} />
        </div>
      );
    }

    // PDF预览
    if (effectiveMime === 'application/pdf') {
      return (
        <div className="preview-pdf">
          <iframe
            src={previewUrl}
            title={fileName}
            width="100%"
            height="100%"
          />
        </div>
      );
    }

    // 音频预览
    if (effectiveMime.startsWith('audio/')) {
      return (
        <div className="preview-audio">
          <div className="audio-player-container">
            <div className="audio-info">
              <div className="audio-icon">🎵</div>
              <div className="audio-details">
                <h3>{fileName}</h3>
                <p>音频文件 - {formatFileSize(fileSize)}</p>
              </div>
            </div>
            <audio 
              controls 
              preload="metadata"
              style={{ width: '100%', marginTop: '20px' }}
            >
              <source src={previewUrl} type={effectiveMime} />
              您的浏览器不支持音频播放。
            </audio>
          </div>
        </div>
      );
    }

    // 视频预览
    if (effectiveMime.startsWith('video/')) {
      return (
        <div className="preview-video">
          <video 
            controls 
            preload="metadata"
            style={{ width: '100%', height: '100%' }}
          >
            <source src={previewUrl} type={effectiveMime} />
            您的浏览器不支持视频播放。
          </video>
        </div>
      );
    }

    // 文本文件预览
    if (effectiveMime.startsWith('text/')) {
      return (
        <div className="preview-text">
          <iframe
            src={previewUrl}
            title={fileName}
            width="100%"
            height="100%"
          />
        </div>
      );
    }

    // 不支持预览的文件类型
    return (
      <div className="preview-unsupported">
        <div className="file-icon">{getFileIcon(effectiveMime)}</div>
        <h3>{fileName}</h3>
        <p>此文件类型不支持预览</p>
        <div className="file-info">
          <span>文件大小: {formatFileSize(fileSize)}</span>
          <span>文件类型: {effectiveMime}</span>
        </div>
        <button 
          className="download-btn"
          onClick={() => window.open(`http://localhost:8000/api/study-resources/${resourceId}/download`, '_blank')}
        >
          下载文件
        </button>
      </div>
    );
  };

  return (
    <div className="resource-preview-overlay" onClick={onClose}>
      <div className="resource-preview-modal" onClick={(e) => e.stopPropagation()}>
        <div className="preview-header">
          <div className="file-info">
            <span className="file-icon">{getFileIcon(getEffectiveMime())}</span>
            <div className="file-details">
              <h3>{fileName}</h3>
              <span className="file-meta">
                {formatFileSize(fileSize)} • {getEffectiveMime()}
              </span>
            </div>
          </div>
          <div className="preview-actions">
            <button 
              className="action-btn download-btn"
              onClick={() => window.open(`http://localhost:8000/api/study-resources/${resourceId}/download`, '_blank')}
              title="下载文件"
            >
              📥
            </button>
            {/* 在新标签打开预览（适用于 PDF/图片/视频等） */}
            {previewUrl && (
              <button 
                className="action-btn"
                onClick={() => window.open(previewUrl, '_blank')}
                title="新标签打开预览"
              >
                🔗
              </button>
            )}
            <button 
              className="action-btn close-btn"
              onClick={onClose}
              title="关闭预览"
            >
              ✕
            </button>
          </div>
        </div>
        
        <div className="preview-content">
          {renderPreview()}
        </div>
      </div>
    </div>
  );
};

export default ResourcePreview;
