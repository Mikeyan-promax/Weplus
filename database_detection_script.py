#!/usr/bin/env python3
"""
数据库检测脚本
用于检测PostgreSQL数据库类型、版本信息和是否为阿里云RDS实例
"""

import os
import sys
import json
import asyncio
import asyncpg
import psycopg2
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 加载环境变量 - 确保从backend目录加载.env文件
backend_dir = os.path.dirname(os.path.abspath(__file__))
if 'backend' not in backend_dir:
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')

env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

class DatabaseDetector:
    """数据库检测器"""
    
    def __init__(self):
        # 从环境变量获取数据库配置
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '5432'))
        self.database = os.getenv('DB_NAME', 'weplus_db')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')
        
        # 打印加载的配置用于调试
        print(f"Debug: 加载的配置信息:")
        print(f"  - DB_HOST: {self.host}")
        print(f"  - DB_PORT: {self.port}")
        print(f"  - DB_NAME: {self.database}")
        print(f"  - DB_USER: {self.user}")
        print(f"  - .env文件路径: {env_path}")
        print(f"  - .env文件存在: {os.path.exists(env_path)}")
        print()
        
        self.detection_results = {
            'timestamp': datetime.now().isoformat(),
            'connection_info': {},
            'server_info': {},
            'database_info': {},
            'performance_metrics': {},
            'cloud_provider': {},
            'errors': []
        }
    
    def detect_connection_info(self):
        """检测连接信息"""
        try:
            self.detection_results['connection_info'] = {
                'host': self.host,
                'port': self.port,
                'database': self.database,
                'user': self.user,
                'connection_string': f"postgresql://{self.user}:***@{self.host}:{self.port}/{self.database}"
            }
            
            # 判断是否为阿里云RDS
            is_aliyun_rds = False
            if 'rds.aliyuncs.com' in self.host:
                is_aliyun_rds = True
            elif 'pgm-' in self.host and '.pg.' in self.host:
                is_aliyun_rds = True
            
            self.detection_results['cloud_provider'] = {
                'is_aliyun_rds': is_aliyun_rds,
                'provider': 'Alibaba Cloud RDS' if is_aliyun_rds else 'Unknown/Local',
                'host_pattern_analysis': {
                    'contains_rds_aliyuncs': 'rds.aliyuncs.com' in self.host,
                    'contains_pgm_prefix': 'pgm-' in self.host,
                    'contains_pg_subdomain': '.pg.' in self.host
                }
            }
            
            print(f"✓ 连接信息检测完成")
            print(f"  - 主机: {self.host}")
            print(f"  - 端口: {self.port}")
            print(f"  - 数据库: {self.database}")
            print(f"  - 云服务商: {self.detection_results['cloud_provider']['provider']}")
            
        except Exception as e:
            error_msg = f"连接信息检测失败: {str(e)}"
            self.detection_results['errors'].append(error_msg)
            print(f"✗ {error_msg}")
    
    async def detect_server_info_async(self):
        """异步检测服务器信息"""
        try:
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            
            # 获取PostgreSQL版本信息
            version_result = await conn.fetchrow("SELECT version();")
            version_full = version_result['version']
            
            # 获取服务器设置
            server_settings = await conn.fetch("""
                SELECT name, setting, unit, category, short_desc 
                FROM pg_settings 
                WHERE name IN (
                    'server_version', 'server_version_num', 'data_directory',
                    'config_file', 'hba_file', 'ident_file', 'external_pid_file',
                    'port', 'max_connections', 'shared_buffers', 'effective_cache_size',
                    'work_mem', 'maintenance_work_mem', 'checkpoint_completion_target',
                    'wal_buffers', 'default_statistics_target', 'random_page_cost',
                    'effective_io_concurrency', 'min_wal_size', 'max_wal_size'
                )
                ORDER BY category, name;
            """)
            
            # 获取数据库大小信息
            db_size_result = await conn.fetchrow("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size,
                       pg_database_size(current_database()) as db_size_bytes;
            """)
            
            # 获取表信息
            table_info = await conn.fetch("""
                SELECT schemaname, tablename, 
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10;
            """)
            
            # 获取连接信息
            connection_info = await conn.fetch("""
                SELECT datname, usename, application_name, client_addr, state, 
                       backend_start, query_start, state_change
                FROM pg_stat_activity 
                WHERE state = 'active'
                ORDER BY backend_start;
            """)
            
            await conn.close()
            
            # 整理服务器信息
            settings_dict = {}
            for setting in server_settings:
                settings_dict[setting['name']] = {
                    'value': setting['setting'],
                    'unit': setting['unit'],
                    'category': setting['category'],
                    'description': setting['short_desc']
                }
            
            self.detection_results['server_info'] = {
                'version_full': version_full,
                'version_short': settings_dict.get('server_version', {}).get('value', 'Unknown'),
                'version_number': settings_dict.get('server_version_num', {}).get('value', 'Unknown'),
                'settings': settings_dict
            }
            
            self.detection_results['database_info'] = {
                'name': self.database,
                'size_pretty': db_size_result['db_size'],
                'size_bytes': db_size_result['db_size_bytes'],
                'tables': [dict(table) for table in table_info],
                'active_connections': len(connection_info),
                'connection_details': [dict(conn) for conn in connection_info]
            }
            
            print(f"✓ 服务器信息检测完成")
            print(f"  - PostgreSQL版本: {self.detection_results['server_info']['version_short']}")
            print(f"  - 数据库大小: {db_size_result['db_size']}")
            print(f"  - 活跃连接数: {len(connection_info)}")
            
        except Exception as e:
            error_msg = f"服务器信息检测失败: {str(e)}"
            self.detection_results['errors'].append(error_msg)
            print(f"✗ {error_msg}")
    
    def detect_performance_metrics(self):
        """检测性能指标"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            cursor = conn.cursor()
            
            # 检测连接延迟
            import time
            start_time = time.time()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            connection_latency = (time.time() - start_time) * 1000  # 毫秒
            
            # 获取数据库统计信息
            cursor.execute("""
                SELECT datname, numbackends, xact_commit, xact_rollback, 
                       blks_read, blks_hit, tup_returned, tup_fetched, 
                       tup_inserted, tup_updated, tup_deleted
                FROM pg_stat_database 
                WHERE datname = %s;
            """, (self.database,))
            
            db_stats = cursor.fetchone()
            
            # 获取缓存命中率
            cursor.execute("""
                SELECT 
                    sum(blks_hit) * 100.0 / sum(blks_hit + blks_read) as cache_hit_ratio
                FROM pg_stat_database;
            """)
            cache_hit_ratio = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            self.detection_results['performance_metrics'] = {
                'connection_latency_ms': round(connection_latency, 2),
                'cache_hit_ratio': round(float(cache_hit_ratio or 0), 2),
                'database_stats': {
                    'active_backends': db_stats[1] if db_stats else 0,
                    'committed_transactions': db_stats[2] if db_stats else 0,
                    'rolled_back_transactions': db_stats[3] if db_stats else 0,
                    'blocks_read': db_stats[4] if db_stats else 0,
                    'blocks_hit': db_stats[5] if db_stats else 0,
                    'tuples_returned': db_stats[6] if db_stats else 0,
                    'tuples_fetched': db_stats[7] if db_stats else 0,
                    'tuples_inserted': db_stats[8] if db_stats else 0,
                    'tuples_updated': db_stats[9] if db_stats else 0,
                    'tuples_deleted': db_stats[10] if db_stats else 0
                }
            }
            
            print(f"✓ 性能指标检测完成")
            print(f"  - 连接延迟: {connection_latency:.2f}ms")
            print(f"  - 缓存命中率: {cache_hit_ratio:.2f}%")
            
        except Exception as e:
            error_msg = f"性能指标检测失败: {str(e)}"
            self.detection_results['errors'].append(error_msg)
            print(f"✗ {error_msg}")
    
    async def run_detection(self):
        """运行完整检测"""
        print("=" * 60)
        print("PostgreSQL 数据库检测脚本")
        print("=" * 60)
        
        # 1. 检测连接信息
        print("\n1. 检测连接信息...")
        self.detect_connection_info()
        
        # 2. 检测服务器信息
        print("\n2. 检测服务器信息...")
        await self.detect_server_info_async()
        
        # 3. 检测性能指标
        print("\n3. 检测性能指标...")
        self.detect_performance_metrics()
        
        # 4. 生成报告
        print("\n4. 生成检测报告...")
        self.generate_report()
    
    def generate_report(self):
        """生成检测报告"""
        try:
            # 保存详细报告到JSON文件
            report_file = f"database_detection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.detection_results, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"✓ 详细报告已保存到: {report_file}")
            
            # 打印摘要报告
            print("\n" + "=" * 60)
            print("检测结果摘要")
            print("=" * 60)
            
            # 基本信息
            print(f"数据库类型: PostgreSQL")
            if self.detection_results['server_info']:
                print(f"版本: {self.detection_results['server_info'].get('version_short', 'Unknown')}")
            
            # 云服务商信息
            cloud_info = self.detection_results['cloud_provider']
            if cloud_info.get('is_aliyun_rds'):
                print(f"云服务商: ✓ 阿里云RDS PostgreSQL")
                print(f"RDS实例主机: {self.host}")
            else:
                print(f"云服务商: ✗ 非阿里云RDS (可能是本地或其他云服务)")
            
            # 连接信息
            print(f"连接主机: {self.host}")
            print(f"连接端口: {self.port}")
            print(f"数据库名: {self.database}")
            
            # 数据库信息
            if self.detection_results['database_info']:
                db_info = self.detection_results['database_info']
                print(f"数据库大小: {db_info.get('size_pretty', 'Unknown')}")
                print(f"活跃连接数: {db_info.get('active_connections', 0)}")
                print(f"用户表数量: {len(db_info.get('tables', []))}")
            
            # 性能指标
            if self.detection_results['performance_metrics']:
                perf = self.detection_results['performance_metrics']
                print(f"连接延迟: {perf.get('connection_latency_ms', 0)}ms")
                print(f"缓存命中率: {perf.get('cache_hit_ratio', 0)}%")
            
            # 错误信息
            if self.detection_results['errors']:
                print(f"\n⚠️  检测过程中发现 {len(self.detection_results['errors'])} 个错误:")
                for i, error in enumerate(self.detection_results['errors'], 1):
                    print(f"  {i}. {error}")
            else:
                print(f"\n✓ 所有检测项目均成功完成")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"✗ 生成报告失败: {str(e)}")

async def main():
    """主函数"""
    detector = DatabaseDetector()
    await detector.run_detection()

if __name__ == "__main__":
    # 检查依赖
    try:
        import asyncpg
        import psycopg2
    except ImportError as e:
        print(f"缺少必要的依赖包: {e}")
        print("请运行: pip install asyncpg psycopg2-binary")
        sys.exit(1)
    
    # 运行检测
    asyncio.run(main())