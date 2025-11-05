"""
数据备份服务
提供系统数据的备份、恢复和管理功能
"""

import os
import json
import shutil
import zipfile
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import logging

# 使用统一的数据库配置
from database.config import get_db_connection
import subprocess

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BackupConfig:
    """备份配置"""
    backup_dir: str = "backups"
    max_backups: int = 10
    compress: bool = True
    include_database: bool = True
    include_files: bool = True
    include_vector_store: bool = True
    backup_interval_hours: int = 24

@dataclass
class BackupInfo:
    """备份信息"""
    id: str
    timestamp: datetime
    size: int  # 备份大小（字节）
    type: str  # 备份类型：full, database, files
    status: str  # 状态：success, failed, in_progress
    file_path: str
    description: str = ""
    error_message: str = ""

class BackupService:
    """数据备份服务"""
    
    def __init__(self, config: BackupConfig = None):
        self.config = config or BackupConfig()
        self.backup_dir = Path(self.config.backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # 文件存储路径
        self.files_dir = Path(__file__).parent.parent.parent / "data" / "uploads"
        self.vector_store_dir = Path(__file__).parent.parent.parent / "data" / "vector_store"
        self.chroma_db_dir = Path(__file__).parent.parent.parent / "data" / "chroma_db"
        
        # 备份历史文件
        self.backup_history_file = self.backup_dir / "backup_history.json"
        
    async def create_full_backup(self, description: str = "") -> BackupInfo:
        """创建完整备份"""
        backup_id = f"full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_info = BackupInfo(
            id=backup_id,
            timestamp=datetime.now(),
            size=0,
            type="full",
            status="in_progress",
            file_path="",
            description=description or "完整系统备份"
        )
        
        try:
            logger.info(f"开始创建完整备份: {backup_id}")
            
            # 创建临时备份目录
            temp_backup_dir = self.backup_dir / f"temp_{backup_id}"
            temp_backup_dir.mkdir(exist_ok=True)
            
            # 备份数据库
            if self.config.include_database:
                await self._backup_database(temp_backup_dir)
            
            # 备份文件
            if self.config.include_files:
                await self._backup_files(temp_backup_dir)
            
            # 备份向量存储
            if self.config.include_vector_store:
                await self._backup_vector_stores(temp_backup_dir)
            
            # 创建备份元数据
            metadata = {
                "backup_id": backup_id,
                "timestamp": backup_info.timestamp.isoformat(),
                "type": "full",
                "description": backup_info.description,
                "config": asdict(self.config)
            }
            
            with open(temp_backup_dir / "backup_metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 压缩备份（如果启用）
            if self.config.compress:
                backup_file = self.backup_dir / f"{backup_id}.zip"
                await self._compress_backup(temp_backup_dir, backup_file)
                backup_info.file_path = str(backup_file)
                backup_info.size = backup_file.stat().st_size
                
                # 删除临时目录
                shutil.rmtree(temp_backup_dir)
            else:
                # 重命名临时目录
                final_backup_dir = self.backup_dir / backup_id
                temp_backup_dir.rename(final_backup_dir)
                backup_info.file_path = str(final_backup_dir)
                backup_info.size = self._get_directory_size(final_backup_dir)
            
            backup_info.status = "success"
            logger.info(f"完整备份创建成功: {backup_id}, 大小: {backup_info.size} 字节")
            
        except Exception as e:
            backup_info.status = "failed"
            backup_info.error_message = str(e)
            logger.error(f"创建完整备份失败: {e}")
            
            # 清理临时文件
            if temp_backup_dir.exists():
                shutil.rmtree(temp_backup_dir)
        
        # 保存备份信息
        await self._save_backup_info(backup_info)
        
        # 清理旧备份
        await self._cleanup_old_backups()
        
        return backup_info
    
    async def create_database_backup(self, description: str = "") -> BackupInfo:
        """创建数据库备份"""
        backup_id = f"db_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_info = BackupInfo(
            id=backup_id,
            timestamp=datetime.now(),
            size=0,
            type="database",
            status="in_progress",
            file_path="",
            description=description or "数据库备份"
        )
        
        try:
            logger.info(f"开始创建数据库备份: {backup_id}")
            
            # 创建备份目录
            backup_dir = self.backup_dir / backup_id
            backup_dir.mkdir(exist_ok=True)
            
            # 备份数据库
            await self._backup_database(backup_dir)
            
            # 创建备份元数据
            metadata = {
                "backup_id": backup_id,
                "timestamp": backup_info.timestamp.isoformat(),
                "type": "database",
                "description": backup_info.description
            }
            
            with open(backup_dir / "backup_metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 压缩备份
            if self.config.compress:
                backup_file = self.backup_dir / f"{backup_id}.zip"
                await self._compress_backup(backup_dir, backup_file)
                backup_info.file_path = str(backup_file)
                backup_info.size = backup_file.stat().st_size
                shutil.rmtree(backup_dir)
            else:
                backup_info.file_path = str(backup_dir)
                backup_info.size = self._get_directory_size(backup_dir)
            
            backup_info.status = "success"
            logger.info(f"数据库备份创建成功: {backup_id}")
            
        except Exception as e:
            backup_info.status = "failed"
            backup_info.error_message = str(e)
            logger.error(f"创建数据库备份失败: {e}")
        
        await self._save_backup_info(backup_info)
        return backup_info
    
    async def _backup_database(self, backup_dir: Path):
        """备份PostgreSQL数据库"""
        db_backup_dir = backup_dir / "database"
        db_backup_dir.mkdir(exist_ok=True)
        
        try:
            # 获取数据库连接信息
            from database.config import DB_CONFIG
            
            # 使用pg_dump导出数据库
            dump_file = db_backup_dir / "weplus_backup.sql"
            
            # 构建pg_dump命令
            pg_dump_cmd = [
                "pg_dump",
                f"--host={DB_CONFIG['host']}",
                f"--port={DB_CONFIG['port']}",
                f"--username={DB_CONFIG['user']}",
                f"--dbname={DB_CONFIG['database']}",
                "--no-password",
                "--verbose",
                "--clean",
                "--if-exists",
                "--create",
                f"--file={dump_file}"
            ]
            
            # 设置环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = DB_CONFIG['password']
            
            # 执行备份命令
            result = subprocess.run(
                pg_dump_cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("PostgreSQL数据库备份完成")
            
            # 同时创建一个仅数据的备份
            data_dump_file = db_backup_dir / "weplus_data_only.sql"
            pg_dump_data_cmd = [
                "pg_dump",
                f"--host={DB_CONFIG['host']}",
                f"--port={DB_CONFIG['port']}",
                f"--username={DB_CONFIG['user']}",
                f"--dbname={DB_CONFIG['database']}",
                "--no-password",
                "--data-only",
                "--verbose",
                f"--file={data_dump_file}"
            ]
            
            subprocess.run(
                pg_dump_data_cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("PostgreSQL数据备份完成")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"pg_dump执行失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            raise Exception(f"数据库备份失败: {e.stderr}")
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            raise
    
    async def _backup_files(self, backup_dir: Path):
        """备份上传的文件"""
        if not self.files_dir.exists():
            logger.warning("文件目录不存在，跳过文件备份")
            return
        
        files_backup_dir = backup_dir / "files"
        shutil.copytree(self.files_dir, files_backup_dir, dirs_exist_ok=True)
        logger.info("文件备份完成")
    
    async def _backup_vector_stores(self, backup_dir: Path):
        """备份向量存储"""
        vector_backup_dir = backup_dir / "vector_stores"
        vector_backup_dir.mkdir(exist_ok=True)
        
        # 备份向量存储目录
        if self.vector_store_dir.exists():
            shutil.copytree(
                self.vector_store_dir, 
                vector_backup_dir / "vector_store", 
                dirs_exist_ok=True
            )
        
        # 备份ChromaDB
        if self.chroma_db_dir.exists():
            shutil.copytree(
                self.chroma_db_dir, 
                vector_backup_dir / "chroma_db", 
                dirs_exist_ok=True
            )
        
        logger.info("向量存储备份完成")
    
    async def _compress_backup(self, source_dir: Path, target_file: Path):
        """压缩备份目录"""
        with zipfile.ZipFile(target_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)
        
        logger.info(f"备份压缩完成: {target_file}")
    
    def _get_directory_size(self, directory: Path) -> int:
        """获取目录大小"""
        total_size = 0
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
    
    async def _save_backup_info(self, backup_info: BackupInfo):
        """保存备份信息"""
        history = await self._load_backup_history()
        history.append(asdict(backup_info))
        
        with open(self.backup_history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2, default=str)
    
    async def _load_backup_history(self) -> List[Dict]:
        """加载备份历史"""
        if not self.backup_history_file.exists():
            return []
        
        try:
            with open(self.backup_history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载备份历史失败: {e}")
            return []
    
    async def get_backup_list(self) -> List[BackupInfo]:
        """获取备份列表"""
        history = await self._load_backup_history()
        backups = []
        
        for item in history:
            # 转换时间戳
            if isinstance(item.get('timestamp'), str):
                item['timestamp'] = datetime.fromisoformat(item['timestamp'])
            
            backups.append(BackupInfo(**item))
        
        # 按时间倒序排列
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        return backups
    
    async def delete_backup(self, backup_id: str) -> bool:
        """删除指定备份"""
        try:
            history = await self._load_backup_history()
            backup_to_delete = None
            
            # 查找要删除的备份
            for i, item in enumerate(history):
                if item['id'] == backup_id:
                    backup_to_delete = item
                    del history[i]
                    break
            
            if not backup_to_delete:
                logger.warning(f"备份不存在: {backup_id}")
                return False
            
            # 删除备份文件
            backup_path = Path(backup_to_delete['file_path'])
            if backup_path.exists():
                if backup_path.is_file():
                    backup_path.unlink()
                else:
                    shutil.rmtree(backup_path)
            
            # 更新历史记录
            with open(self.backup_history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"备份删除成功: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除备份失败: {e}")
            return False
    
    async def _cleanup_old_backups(self):
        """清理旧备份"""
        try:
            backups = await self.get_backup_list()
            
            if len(backups) <= self.config.max_backups:
                return
            
            # 删除超出数量限制的旧备份
            old_backups = backups[self.config.max_backups:]
            for backup in old_backups:
                await self.delete_backup(backup.id)
            
            logger.info(f"清理了 {len(old_backups)} 个旧备份")
            
        except Exception as e:
            logger.error(f"清理旧备份失败: {e}")
    
    async def restore_database_backup(self, backup_path: Path) -> bool:
        """恢复数据库备份"""
        try:
            from database.config import DB_CONFIG
            
            sql_file = backup_path / "database" / "weplus_backup.sql"
            if not sql_file.exists():
                logger.error("数据库备份文件不存在")
                return False
            
            # 使用psql恢复数据库
            psql_cmd = [
                "psql",
                f"--host={DB_CONFIG['host']}",
                f"--port={DB_CONFIG['port']}",
                f"--username={DB_CONFIG['user']}",
                f"--dbname={DB_CONFIG['database']}",
                "--no-password",
                f"--file={sql_file}"
            ]
            
            # 设置环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = DB_CONFIG['password']
            
            # 执行恢复命令
            result = subprocess.run(
                psql_cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("数据库恢复完成")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"数据库恢复失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"数据库恢复失败: {e}")
            return False
    
    async def restore_backup(self, backup_id: str) -> bool:
        """恢复备份"""
        try:
            backups = await self.get_backup_list()
            backup_to_restore = None
            
            for backup in backups:
                if backup.id == backup_id:
                    backup_to_restore = backup
                    break
            
            if not backup_to_restore:
                logger.error(f"备份不存在: {backup_id}")
                return False
            
            logger.info(f"开始恢复备份: {backup_id}")
            
            backup_path = Path(backup_to_restore.file_path)
            
            if backup_path.suffix == '.zip':
                # 解压备份
                temp_restore_dir = self.backup_dir / f"restore_{backup_id}"
                temp_restore_dir.mkdir(exist_ok=True)
                
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_restore_dir)
                
                restore_source = temp_restore_dir
            else:
                restore_source = backup_path
            
            # 恢复数据库
            if (restore_source / "database").exists():
                await self.restore_database_backup(restore_source)
            
            # 恢复文件
            files_backup_dir = restore_source / "files"
            if files_backup_dir.exists():
                if self.files_dir.exists():
                    shutil.rmtree(self.files_dir)
                shutil.copytree(files_backup_dir, self.files_dir)
            
            # 恢复向量存储
            vector_backup_dir = restore_source / "vector_stores"
            if vector_backup_dir.exists():
                if (vector_backup_dir / "vector_store").exists():
                    if self.vector_store_dir.exists():
                        shutil.rmtree(self.vector_store_dir)
                    shutil.copytree(
                        vector_backup_dir / "vector_store", 
                        self.vector_store_dir
                    )
                
                if (vector_backup_dir / "chroma_db").exists():
                    if self.chroma_db_dir.exists():
                        shutil.rmtree(self.chroma_db_dir)
                    shutil.copytree(
                        vector_backup_dir / "chroma_db", 
                        self.chroma_db_dir
                    )
            
            # 清理临时文件
            if backup_path.suffix == '.zip' and temp_restore_dir.exists():
                shutil.rmtree(temp_restore_dir)
            
            logger.info(f"备份恢复成功: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            return False
    
    async def get_backup_statistics(self) -> Dict[str, Any]:
        """获取备份统计信息"""
        backups = await self.get_backup_list()
        
        total_size = sum(backup.size for backup in backups)
        successful_backups = [b for b in backups if b.status == "success"]
        failed_backups = [b for b in backups if b.status == "failed"]
        
        # 按类型统计
        type_stats = {}
        for backup in backups:
            type_stats[backup.type] = type_stats.get(backup.type, 0) + 1
        
        # 最近备份时间
        last_backup = backups[0] if backups else None
        
        return {
            "total_backups": len(backups),
            "successful_backups": len(successful_backups),
            "failed_backups": len(failed_backups),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "backup_types": type_stats,
            "last_backup_time": last_backup.timestamp if last_backup else None,
            "oldest_backup_time": backups[-1].timestamp if backups else None
        }

# 全局备份服务实例
backup_service = BackupService()

# 定时备份任务
async def scheduled_backup_task():
    """定时备份任务"""
    while True:
        try:
            logger.info("执行定时备份任务")
            await backup_service.create_full_backup("定时自动备份")
            
            # 等待下次备份
            await asyncio.sleep(backup_service.config.backup_interval_hours * 3600)
            
        except Exception as e:
            logger.error(f"定时备份任务失败: {e}")
            # 出错后等待1小时再重试
            await asyncio.sleep(3600)

if __name__ == "__main__":
    # 测试备份服务
    async def test_backup():
        # 创建测试备份
        backup_info = await backup_service.create_full_backup("测试备份")
        print(f"备份结果: {backup_info}")
        
        # 获取备份列表
        backups = await backup_service.get_backup_list()
        print(f"备份列表: {len(backups)} 个备份")
        
        # 获取统计信息
        stats = await backup_service.get_backup_statistics()
        print(f"备份统计: {stats}")
    
    asyncio.run(test_backup())