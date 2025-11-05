"""
WePlus 核心配置管理
管理环境变量、数据库连接、API密钥等配置
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Union
from pydantic import field_validator
import os

class Settings(BaseSettings):
    """应用配置类"""
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")
    
    # 应用基础配置
    APP_NAME: str = "WePlus API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: Optional[str] = None
    POSTGRES_USER: str = "weplus"
    POSTGRES_PASSWORD: str = "weplus123"
    POSTGRES_DB: str = "weplus_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    # Redis配置（用于缓存）
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    
    # AI模型配置
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    
    # OpenAI配置（备用）
    OPENAI_API_KEY: Optional[str] = None
    
    # 向量存储配置
    VECTOR_DIMENSION: int = 1536  # OpenAI embedding维度
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
    
    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".md"]
    
    # JWT配置
    SECRET_KEY: str = "weplus-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS配置
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:5174"]

    # 日志与可观测性
    ENABLE_JSON_LOGGING: bool = True
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = False

    # 访问控制与限流
    REQUEST_RATE_LIMIT_ENABLED: bool = False
    REQUEST_RATE_LIMIT_PER_MINUTE: int = 60
    ADMIN_IP_WHITELIST: List[str] = []

    # 管理后台API安全模式开关
    # 为 True 时，仪表盘/RAG/文件统计等只读接口在发生异常时返回结构化的空数据（HTTP 200）
    # 为 False 时，直接抛出异常以便在生产环境暴露问题并触发告警
    ADMIN_API_SAFE_MODE: bool = True
    
    @property
    def database_url(self) -> str:
        """构建数据库连接URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # 注意：Pydantic v2 中不再同时支持 Config 和 model_config，这里使用 model_config

    # 兼容从 .env 加载的人性化配置格式
    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    def _parse_allowed_extensions(cls, v: Union[str, List[str]]):
        """支持逗号分隔字符串或JSON数组形式
        例如：".pdf,.txt,.docx" 或 [".pdf", ".txt"]
        """
        if isinstance(v, str):
            items = [s.strip() for s in v.split(',') if s.strip()]
            return items
        return v

    @field_validator("MAX_FILE_SIZE", mode="before")
    def _parse_max_file_size(cls, v: Union[str, int, float]):
        """支持诸如 50MB / 10M / 1024K / 1048576 这类写法到字节数
        若为数字则直接返回整型字节数
        """
        if v is None:
            return v
        if isinstance(v, (int, float)):
            return int(v)
        s = str(v).strip().upper()
        # 去掉末尾的 'B' 以兼容如 '50MB'/'1024KB'
        if s.endswith('B') and not s.endswith('DB'):
            s = s[:-1]
        def _to_int(num_str: str, multiplier: int = 1) -> int:
            try:
                return int(float(num_str) * multiplier)
            except ValueError:
                # 回退：尝试直接转 int
                return int(num_str)
        if s.endswith('KB') or s.endswith('K'):
            return _to_int(s.replace('KB', '').replace('K', ''), 1024)
        if s.endswith('MB') or s.endswith('M'):
            return _to_int(s.replace('MB', '').replace('M', ''), 1024 * 1024)
        if s.endswith('GB') or s.endswith('G'):
            return _to_int(s.replace('GB', '').replace('G', ''), 1024 * 1024 * 1024)
        # 纯数字字符串
        return int(s)

    @field_validator("ALLOWED_ORIGINS", mode="before")
    def _parse_allowed_origins(cls, v: Union[str, List[str]]):
        """支持逗号分隔或JSON数组，统一转List[str]"""
        if isinstance(v, str):
            items = [s.strip() for s in v.split(',') if s.strip()]
            return items
        return v

    @field_validator("ADMIN_IP_WHITELIST", mode="before")
    def _parse_admin_ip_whitelist(cls, v: Union[str, List[str]]):
        """支持逗号分隔字符串或JSON数组形式的IP白名单"""
        if isinstance(v, str):
            items = [s.strip() for s in v.split(',') if s.strip()]
            return items
        return v

# 创建全局配置实例
settings = Settings()

# 创建必要的目录
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
