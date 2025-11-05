"""
邮件服务模块
实现邮件发送和验证码功能

说明：
- 原有实现在模块导入时立即初始化 FastMail/ConnectionConfig（依赖 fastapi-mail 与 Pydantic 版本兼容）。
- 为避免在应用启动阶段因依赖不兼容或缺失环境变量导致崩溃，这里改为惰性初始化：仅在实际发送邮件时才初始化并捕获异常。
"""

import random
import string
import asyncio
from typing import Optional
from pydantic import EmailStr
import os
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
from app.core.config import settings

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        """初始化邮件服务（惰性初始化，不在导入阶段触发外部依赖）。

        - 仅加载环境变量并准备内存存储结构；
        - 不立即创建 ConnectionConfig/FastMail，避免因 fastapi-mail 与 Pydantic 不兼容或环境变量缺失导致应用启动失败；
        - 真正需要发送邮件时再执行初始化，并做好异常捕获与降级。
        """
        # 邮件配置
        self.mail_username = os.getenv("MAIL_USERNAME")
        self.mail_password = os.getenv("MAIL_PASSWORD")
        self.mail_from = os.getenv("MAIL_FROM", self.mail_username)
        self.mail_port = int(os.getenv("MAIL_PORT", "587"))
        self.mail_server = os.getenv("MAIL_SERVER", "smtp.163.com")
        self.mail_from_name = os.getenv("MAIL_FROM_NAME", "WePlus 校园助手")
        self.mail_starttls = os.getenv("MAIL_STARTTLS", "True").lower() == "true"
        self.mail_ssl_tls = os.getenv("MAIL_SSL_TLS", "False").lower() == "true"
        # 开发模式开关（来自全局配置）
        self.debug_mode = bool(getattr(settings, "DEBUG", False))

        # 内存存储验证码和冷却时间
        self.verification_codes = {}  # {email_purpose: {"code": str, "expires": datetime}}
        self.cooldown_times = {}      # {email_purpose: datetime}

        # 惰性初始化相关标记与对象
        self.conf = None
        self.fastmail = None
        self.init_error: Optional[str] = None

    def ensure_mail_client(self) -> bool:
        """确保邮件客户端已初始化（惰性初始化）。

        返回：
        - True：初始化成功，可以正常发送邮件
        - False：初始化失败，错误信息保存在 self.init_error

        说明：
        - 这里采用内部延迟导入 fastapi_mail，避免其在与 Pydantic v2 不兼容时影响应用启动；
        - 初始化失败时仅影响邮件发送功能，不影响整个应用的健康检查与运行。
        """
        if self.fastmail is not None:
            return True
        try:
            # 内部延迟导入，避免不兼容导致模块级崩溃
            from fastapi_mail import FastMail, ConnectionConfig

            self.conf = ConnectionConfig(
                MAIL_USERNAME=self.mail_username,
                MAIL_PASSWORD=self.mail_password,
                MAIL_FROM=self.mail_from,
                MAIL_PORT=self.mail_port,
                MAIL_SERVER=self.mail_server,
                MAIL_FROM_NAME=self.mail_from_name,
                MAIL_STARTTLS=self.mail_starttls,
                MAIL_SSL_TLS=self.mail_ssl_tls,
                USE_CREDENTIALS=True,
                VALIDATE_CERTS=True
            )
            self.fastmail = FastMail(self.conf)
            self.init_error = None
            return True
        except Exception as e:
            # 捕获初始化错误，记录并降级
            self.fastmail = None
            self.init_error = str(e)
            logger.error(f"初始化邮件客户端失败: {self.init_error}")
            return False
    
    def generate_verification_code(self, length: int = 6) -> str:
        """生成验证码"""
        return ''.join(random.choices(string.digits, k=length))
    
    def _clean_expired_codes(self):
        """清理过期的验证码"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, data in self.verification_codes.items():
            if current_time > data["expires"]:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.verification_codes[key]
    
    def _clean_expired_cooldowns(self):
        """清理过期的冷却时间"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, expires in self.cooldown_times.items():
            if current_time > expires:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cooldown_times[key]

    async def send_verification_code(self, email: EmailStr, purpose: str = "register") -> dict:
        """
        发送验证码邮件
        
        Args:
            email: 邮箱地址
            purpose: 验证码用途 (register, login, reset_password)
            
        Returns:
            dict: 发送结果
        """
        try:
            # 清理过期数据
            self._clean_expired_codes()
            self._clean_expired_cooldowns()
            
            # 检查冷却时间
            cooldown_key = f"{email}:{purpose}"
            current_time = datetime.now()
            
            if cooldown_key in self.cooldown_times:
                remaining_time = (self.cooldown_times[cooldown_key] - current_time).total_seconds()
                if remaining_time > 0:
                    return {
                        "success": False,
                        "message": f"请等待 {int(remaining_time)} 秒后再次发送",
                        "code": "COOLDOWN_ACTIVE",
                        "remaining_time": int(remaining_time)
                    }
            
            # 生成验证码
            verification_code = self.generate_verification_code()
            
            # 根据用途设置邮件内容
            purpose_text = {
                "register": "注册",
                "login": "登录",
                "reset_password": "重置密码"
            }.get(purpose, "验证")
            
            # HTML邮件模板
            html_content = f"""
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif; background-color: #f9f9f9;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; VARCHAR-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">WePlus 校园助手</h1>
                    <p style="color: #e8e8e8; margin: 10px 0 0 0; font-size: 16px;">{purpose_text}验证码</p>
                </div>
                
                <div style="background: white; padding: 40px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h2 style="color: #333; margin-bottom: 20px; font-size: 24px;">您的验证码</h2>
                    <p style="color: #666; font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                        您正在进行{purpose_text}操作，请使用以下验证码完成验证：
                    </p>
                    
                    <div style="background: #f8f9fa; border: 2px dashed #667eea; padding: 20px; VARCHAR-align: center; border-radius: 8px; margin: 30px 0;">
                        <span style="font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                            {verification_code}
                        </span>
                    </div>
                    
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 6px; margin: 20px 0;">
                        <p style="color: #856404; margin: 0; font-size: 14px;">
                            <strong>⚠️ 重要提醒：</strong><br>
                            • 验证码有效期为 15 分钟<br>
                            • 请勿将验证码告诉他人<br>
                            • 如非本人操作，请忽略此邮件
                        </p>
                    </div>
                </div>
                
                <div style="VARCHAR-align: center; margin-top: 30px; color: #999; font-size: 12px;">
                    <p>此邮件由 WePlus 校园助手系统自动发送，请勿回复</p>
                    <p>© 2025 WePlus研发团队版权所有 | 让校园生活更智能</p>
                </div>
            </div>
            """
            
            # 存储验证码到内存（15分钟过期）
            verification_key = f"{email}:{purpose}"
            expires_at = current_time + timedelta(minutes=15)
            self.verification_codes[verification_key] = {
                "code": verification_code,
                "expires": expires_at
            }
            
            # 设置发送冷却期（60秒）
            self.cooldown_times[cooldown_key] = current_time + timedelta(seconds=60)
            
            # 开发模式：直接回显验证码，不实际发送邮件
            if self.debug_mode:
                logger.info(f"[DEBUG] 已生成验证码但未发送邮件: {email} 用途：{purpose}")
                return {
                    "success": True,
                    "message": "开发模式：验证码已生成（未实际发送）",
                    "code": "DEV_MODE_CODE",
                    "dev": {
                        "verification_code": verification_code,
                        "expires_at": expires_at.isoformat(),
                        "cooldown_seconds": 60
                    }
                }

            # 非调试模式：尝试初始化邮件客户端并发送
            if not self.ensure_mail_client():
                # 初始化失败，返回可解释的错误信息，不抛出异常以保证接口稳定
                return {
                    "success": False,
                    "message": "邮件服务初始化失败，请稍后重试",
                    "code": "INIT_FAILED",
                    "error": self.init_error
                }

            try:
                # 延迟导入消息类型定义
                from fastapi_mail import MessageSchema, MessageType

                message = MessageSchema(
                    subject=f"WePlus 校园助手 - {purpose_text}验证码",
                    recipients=[email],
                    body=html_content,
                    subtype=MessageType.html
                )
                await self.fastmail.send_message(message)
                logger.info(f"验证码邮件已发送到 {email}，用途：{purpose}")
                return {
                    "success": True,
                    "message": "验证码已发送到您的邮箱，请查收",
                    "code": "EMAIL_SENT"
                }
            except Exception as send_err:
                logger.error(f"发送邮件失败（非调试模式）: {str(send_err)}")
                return {
                    "success": False,
                    "message": "邮件发送失败，请稍后重试",
                    "code": "SEND_FAILED",
                    "error": str(send_err)
                }
            
        except Exception as e:
            logger.error(f"发送验证码邮件失败: {str(e)}")
            return {
                "success": False,
                "message": "邮件发送失败，请稍后重试",
                "code": "SEND_FAILED",
                "error": str(e)
            }
    
    async def verify_code(self, email: EmailStr, code: str, purpose: str = "register", delete_on_success: bool = True) -> dict:
        """
        验证验证码
        
        Args:
            email: 邮箱地址
            code: 验证码
            purpose: 验证码用途
            delete_on_success: 验证成功后是否删除验证码
            
        Returns:
            dict: 验证结果
        """
        try:
            # 清理过期数据
            self._clean_expired_codes()
            
            verification_key = f"{email}:{purpose}"
            
            # 检查验证码是否存在
            if verification_key not in self.verification_codes:
                return {
                    "success": False,
                    "message": "验证码不存在或已过期",
                    "code": "CODE_NOT_FOUND"
                }
            
            stored_data = self.verification_codes[verification_key]
            current_time = datetime.now()
            
            # 检查是否过期
            if current_time > stored_data["expires"]:
                del self.verification_codes[verification_key]
                return {
                    "success": False,
                    "message": "验证码已过期",
                    "code": "CODE_EXPIRED"
                }
            
            # 验证验证码
            if code != stored_data["code"]:
                return {
                    "success": False,
                    "message": "验证码错误",
                    "code": "CODE_INVALID"
                }
            
            # 验证成功，根据参数决定是否删除验证码
            if delete_on_success:
                del self.verification_codes[verification_key]
            
            logger.info(f"邮箱 {email} 验证码验证成功，用途：{purpose}")
            
            return {
                "success": True,
                "message": "验证码验证成功",
                "code": "VERIFICATION_SUCCESS"
            }
            
        except Exception as e:
            logger.error(f"验证码验证失败: {str(e)}")
            return {
                "success": False,
                "message": "验证失败，请稍后重试",
                "code": "VERIFICATION_FAILED",
                "error": str(e)
            }

    async def consume_verification_code(self, email: EmailStr, code: str, purpose: str = "register") -> dict:
        """
        消费验证码（验证并删除）
        
        Args:
            email: 邮箱地址
            code: 验证码
            purpose: 验证码用途
            
        Returns:
            dict: 验证结果
        """
        return await self.verify_code(email, code, purpose, delete_on_success=True)
    
    async def check_email_cooldown(self, email: EmailStr, purpose: str = "register") -> dict:
        """
        检查邮箱发送冷却时间
        
        Args:
            email: 邮箱地址
            purpose: 验证码用途
            
        Returns:
            dict: 冷却状态
        """
        try:
            # 清理过期数据
            self._clean_expired_cooldowns()
            
            cooldown_key = f"{email}:{purpose}"
            current_time = datetime.now()
            
            if cooldown_key in self.cooldown_times:
                remaining_time = (self.cooldown_times[cooldown_key] - current_time).total_seconds()
                if remaining_time > 0:
                    return {
                        "success": False,
                        "message": f"请等待 {int(remaining_time)} 秒后再次发送",
                        "code": "COOLDOWN_ACTIVE",
                        "remaining_time": int(remaining_time)
                    }
            
            return {
                "success": True,
                "message": "可以发送验证码",
                "code": "COOLDOWN_READY"
            }
            
        except Exception as e:
            logger.error(f"检查冷却时间失败: {str(e)}")
            return {
                "success": False,
                "message": "检查失败",
                "code": "CHECK_ERROR",
                "error": str(e)
            }

# 创建全局邮件服务实例
email_service = EmailService()
