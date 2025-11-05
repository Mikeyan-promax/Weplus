/**
 * 文档管理API服务
 * 提供文档、分类、标签的CRUD操作和高级搜索功能
 */

// 使用相对路径基准，避免硬编码端口；通过同源或反向代理访问后端
const API_BASE_URL = '';

// 类型定义
export interface Document {
  id: string;
  original_filename: string;
  file_path: string;
  file_type: string;
  file_size: number;
  created_at: string;
  processing_status: string;
  category_id?: number;
  tags?: Tag[];
  category?: Category;
}

export interface Category {
  id: number;
  name: string;
  description?: string;
  color?: string;
  created_at: string;
}

export interface Tag {
  id: number;
  name: string;
  color?: string;
  created_at: string;
}

export interface DocumentListResponse {
  success: boolean;
  message: string;
  data: {
    documents: Document[];
    pagination: {
      current_page: number;
      total_pages: number;
      total_count: number;
      page_size: number;
    };
  };
}

export interface SearchParams {
  search_term?: string;
  category_id?: number;
  tag_ids?: number[];
  file_type?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  limit?: number;
}

export interface BatchOperationRequest {
  document_ids: string[];
  operation: 'delete' | 'category' | 'tags';
  category_id?: number;
  tag_ids?: number[];
}

class DocumentApiService {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
    };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: '请求失败' }));
      throw new Error(errorData.message || `HTTP ${response.status}`);
    }
    return response.json();
  }

  // ==================== 文档管理 ====================

  /**
   * 获取文档列表：相对路径 `${API_BASE_URL}/api/rag/documents`，适配不同部署端口
   */
  async getDocuments(params: {
    offset?: number;
    limit?: number;
    category_id?: number;
    tag_ids?: number[];
    search?: string;
    sort_by?: string;
    sort_order?: string;
  } = {}): Promise<DocumentListResponse> {
    const queryParams = new URLSearchParams();
    
    if (params.offset !== undefined) queryParams.append('offset', params.offset.toString());
    if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params.category_id !== undefined) queryParams.append('category_id', params.category_id.toString());
    if (params.tag_ids && params.tag_ids.length > 0) queryParams.append('tag_ids', params.tag_ids.join(','));
    if (params.search) queryParams.append('search', params.search);
    if (params.sort_by) queryParams.append('sort_by', params.sort_by);
    if (params.sort_order) queryParams.append('sort_order', params.sort_order);

    const response = await fetch(`${API_BASE_URL}/api/rag/documents?${queryParams}`, {
      headers: this.getAuthHeaders(),
    });

    // RAG API返回格式: { documents: [...], total_count: number }
    // 需要适配到前端期望格式: { success: boolean, message: string, data: { documents: [...], pagination: {...} } }
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const ragData = await response.json();
    
    // 转换RAG API数据格式到前端期望格式
    const adaptedResponse: DocumentListResponse = {
      success: true,
      message: 'Documents retrieved successfully',
      data: {
        documents: ragData.documents.map((doc: any) => ({
          id: doc.id,
          original_filename: doc.title || '未命名文档',
          file_path: '',
          file_type: 'document',
          file_size: doc.content_length || 0,
          created_at: doc.processed_at || new Date().toISOString(),
          processing_status: 'completed',
          category_id: undefined,
          tags: [],
          category: undefined
        })),
        pagination: {
          current_page: Math.floor((params.offset || 0) / (params.limit || 20)) + 1,
          total_pages: Math.ceil((ragData.total_count || 0) / (params.limit || 20)),
          total_count: ragData.total_count || 0,
          page_size: params.limit || 20
        }
      }
    };

    return adaptedResponse;
  }

  /**
   * 上传文档：相对路径 `${API_BASE_URL}/api/documents/upload`
   */
  async uploadDocument(file: File, metadata?: {
    category_id?: number;
    tag_ids?: number[];
    description?: string;
  }): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (metadata?.category_id) {
      formData.append('category_id', metadata.category_id.toString());
    }
    if (metadata?.tag_ids && metadata.tag_ids.length > 0) {
      formData.append('tag_ids', JSON.stringify(metadata.tag_ids));
    }
    if (metadata?.description) {
      formData.append('description', metadata.description);
    }

    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
      method: 'POST',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: formData,
    });

    return this.handleResponse(response);
  }

  /**
   * 删除文档：相对路径 `${API_BASE_URL}/api/documents/${documentId}`
   */
  async deleteDocument(documentId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * 更新文档：相对路径 `${API_BASE_URL}/api/documents/${documentId}`
   */
  async updateDocument(documentId: string, data: {
    filename?: string;
    category_id?: number;
    tag_ids?: number[];
    metadata?: Record<string, any>;
  }): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse(response);
  }

  /**
   * 批量操作：相对路径 `${API_BASE_URL}/api/documents/batch}`
   */
  async batchOperation(request: BatchOperationRequest): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/documents/batch`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    });

    return this.handleResponse(response);
  }

  /**
   * 高级搜索
   */
  async advancedSearch(params: SearchParams): Promise<DocumentListResponse> {
    const queryParams = new URLSearchParams();
    
    if (params.search_term) queryParams.append('search_term', params.search_term);
    if (params.category_id !== undefined) queryParams.append('category_id', params.category_id.toString());
    if (params.tag_ids && params.tag_ids.length > 0) queryParams.append('tag_ids', params.tag_ids.join(','));
    if (params.file_type) queryParams.append('file_type', params.file_type);
    if (params.status) queryParams.append('status', params.status);
    if (params.date_from) queryParams.append('date_from', params.date_from);
    if (params.date_to) queryParams.append('date_to', params.date_to);
    if (params.page !== undefined) queryParams.append('page', params.page.toString());
    if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());

    const response = await fetch(`${API_BASE_URL}/api/documents/advanced-search?${queryParams}`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse<DocumentListResponse>(response);
  }

  // ==================== 分类管理 ====================

  /**
   * 获取分类列表
   */
  async getCategories(): Promise<{ success: boolean; data: Category[] }> {
    const response = await fetch(`${API_BASE_URL}/api/documents/categories`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * 创建分类
   */
  async createCategory(data: {
    name: string;
    description?: string;
    color?: string;
  }): Promise<{ success: boolean; data: Category }> {
    const response = await fetch(`${API_BASE_URL}/api/documents/categories`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse(response);
  }

  /**
   * 更新分类
   */
  async updateCategory(categoryId: number, data: {
    name?: string;
    description?: string;
    color?: string;
  }): Promise<{ success: boolean; data: Category }> {
    const response = await fetch(`${API_BASE_URL}/api/documents/categories/${categoryId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse(response);
  }

  /**
   * 删除分类
   */
  async deleteCategory(categoryId: number): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/documents/categories/${categoryId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse(response);
  }

  // ==================== 标签管理 ====================

  /**
   * 获取标签列表
   */
  async getTags(): Promise<{ success: boolean; data: Tag[] }> {
    const response = await fetch(`${API_BASE_URL}/api/documents/tags`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * 创建标签
   */
  async createTag(data: {
    name: string;
    color?: string;
  }): Promise<{ success: boolean; data: Tag }> {
    const response = await fetch(`${API_BASE_URL}/api/documents/tags`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse(response);
  }

  /**
   * 删除标签
   */
  async deleteTag(tagId: number): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/documents/tags/${tagId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse(response);
  }
}

// 导出默认实例
const documentApi = new DocumentApiService();
export { documentApi };
export default documentApi;
