#!/usr/bin/env python3
"""
数据库初始化脚本

该脚本提供数据库创建、表设置、示例数据插入和数据库清理功能。
支持命令行参数控制不同操作模式。
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from src.app import create_app, db
from src.models.task import Task
from src.models.address_info import AddressInfo
from src.config import get_config
from src.utils.database import init_database, test_connection

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self, config_name: Optional[str] = None):
        """
        初始化数据库初始化器
        
        Args:
            config_name: 配置名称 (development, production, testing)
        """
        self.config_name = config_name or 'development'
        self.app = None
        self.config = None
    
    def setup(self) -> None:
        """设置应用和配置"""
        try:
            self.app = create_app(self.config_name)
            self.config = get_config(self.config_name)
            logger.info(f"应用配置已加载: {self.config_name}")
        except Exception as e:
            logger.error(f"应用设置失败: {e}")
            raise
    
    def create_tables(self) -> None:
        """创建数据库表"""
        if not self.app:
            self.setup()
        
        try:
            with self.app.app_context():
                logger.info("开始创建数据库表...")
                db.create_all()
                logger.info("数据库表创建成功")
        except SQLAlchemyError as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
        except Exception as e:
            logger.error(f"创建数据库表时发生未知错误: {e}")
            raise
    
    def drop_tables(self) -> None:
        """删除所有数据库表"""
        if not self.app:
            self.setup()
        
        try:
            with self.app.app_context():
                logger.warning("开始删除数据库表...")
                db.drop_all()
                logger.warning("数据库表删除成功")
        except SQLAlchemyError as e:
            logger.error(f"删除数据库表失败: {e}")
            raise
        except Exception as e:
            logger.error(f"删除数据库表时发生未知错误: {e}")
            raise
    
    def insert_sample_data(self) -> None:
        """插入示例数据"""
        if not self.app:
            self.setup()
        
        try:
            with self.app.app_context():
                logger.info("开始插入示例数据...")
                
                # 检查是否已存在数据
                existing_tasks = Task.query.count()
                existing_addresses = AddressInfo.query.count()
                
                if existing_tasks > 0 or existing_addresses > 0:
                    logger.info(f"数据库中已存在数据 (任务: {existing_tasks}, 地址: {existing_addresses})")
                    # 在非交互环境中，如果存在数据则跳过插入
                    logger.info("数据库中已存在数据，跳过示例数据插入")
                    return
                
                # 插入示例任务数据
                sample_tasks = [
                    Task(
                        url="https://example.com/api/addresses",
                        method="GET",
                        headers={"User-Agent": "AddressCrawler/1.0"},
                        total_num=100,
                        timeout=30,
                        status="pending"
                    ),
                    Task(
                        url="https://api.example.com/locations",
                        method="POST",
                        body='{"city": "Shanghai", "country": "China"}',
                        headers={
                            "User-Agent": "AddressCrawler/1.0",
                            "Content-Type": "application/json"
                        },
                        total_num=50,
                        timeout=60,
                        status="running"
                    ),
                    Task(
                        url="https://test.com/addresses/123",
                        method="GET",
                        total_num=25,
                        timeout=30,
                        status="completed",
                        visited_num=25
                    )
                ]
                
                for task in sample_tasks:
                    db.session.add(task)
                
                # 插入示例地址数据
                sample_addresses = [
                    AddressInfo(
                        address="123 Main Street",
                        telephone="+1-555-123-4567",
                        city="New York",
                        zip_code="10001",
                        state="NY",
                        state_full="New York",
                        country="USA",
                        source_url="https://example.com/addresses/123"
                    ),
                    AddressInfo(
                        address="456 Nanjing Road",
                        telephone="+86-21-1234-5678",
                        city="Shanghai",
                        zip_code="200000",
                        state="SH",
                        state_full="Shanghai",
                        country="China",
                        source_url="https://example.com/addresses/456"
                    ),
                    AddressInfo(
                        address="789 Oxford Street",
                        telephone="+44-20-1234-5678",
                        city="London",
                        zip_code="W1D 1BS",
                        state="ENG",
                        state_full="England",
                        country="UK",
                        source_url="https://example.com/addresses/789"
                    ),
                    AddressInfo(
                        address="321 Champs-Élysées",
                        telephone="+33-1-1234-5678",
                        city="Paris",
                        zip_code="75008",
                        state="IDF",
                        state_full="Île-de-France",
                        country="France",
                        source_url="https://example.com/addresses/321"
                    )
                ]
                
                for address in sample_addresses:
                    db.session.add(address)
                
                # 提交事务
                db.session.commit()
                
                logger.info(f"示例数据插入成功 (任务: {len(sample_tasks)}, 地址: {len(sample_addresses)})")
                
        except SQLAlchemyError as e:
            logger.error(f"插入示例数据失败: {e}")
            if self.app and hasattr(self.app, 'app_context'):
                with self.app.app_context():
                    db.session.rollback()
            raise
        except Exception as e:
            logger.error(f"插入示例数据时发生未知错误: {e}")
            if self.app and hasattr(self.app, 'app_context'):
                with self.app.app_context():
                    db.session.rollback()
            raise
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            # 使用utils.database模块的测试函数
            init_database()
            result = test_connection()
            if result:
                logger.info("数据库连接测试成功")
            else:
                logger.error("数据库连接测试失败")
            return result
        except Exception as e:
            logger.error(f"数据库连接测试出错: {e}")
            return False
    
    def reset_database(self) -> None:
        """重置数据库（删除并重新创建）"""
        logger.warning("开始重置数据库...")
        try:
            self.drop_tables()
            self.create_tables()
            logger.info("数据库重置成功")
        except Exception as e:
            logger.error(f"数据库重置失败: {e}")
            raise
    
    def show_status(self) -> None:
        """显示数据库状态"""
        if not self.app:
            self.setup()
        
        try:
            with self.app.app_context():
                logger.info("数据库状态:")
                logger.info(f"数据库URL: {self.config.DATABASE_URL}")
                
                # 获取表信息
                task_count = Task.query.count()
                address_count = AddressInfo.query.count()
                
                logger.info(f"任务表记录数: {task_count}")
                logger.info(f"地址表记录数: {address_count}")
                
                # 获取任务状态统计
                if task_count > 0:
                    status_stats = db.session.query(
                        Task.status, db.func.count(Task.id)
                    ).group_by(Task.status).all()
                    
                    logger.info("任务状态统计:")
                    for status, count in status_stats:
                        logger.info(f"  {status}: {count}")
                
                # 获取地址国家统计
                if address_count > 0:
                    country_stats = db.session.query(
                        AddressInfo.country, db.func.count(AddressInfo.id)
                    ).group_by(AddressInfo.country).all()
                    
                    logger.info("地址国家统计:")
                    for country, count in country_stats:
                        logger.info(f"  {country or 'Unknown'}: {count}")
                        
        except Exception as e:
            logger.error(f"获取数据库状态失败: {e}")
            raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="数据库初始化脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 创建数据库表
  python scripts/init_db.py --create
  
  # 插入示例数据
  python scripts/init_db.py --sample-data
  
  # 重置数据库（删除并重新创建）
  python scripts/init_db.py --reset
  
  # 显示数据库状态
  python scripts/init_db.py --status
  
  # 测试数据库连接
  python scripts/init_db.py --test
  
  # 完整初始化（创建表 + 插入示例数据）
  python scripts/init_db.py --full-init
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        choices=['development', 'production', 'testing'],
        default='development',
        help='配置环境 (默认: development)'
    )
    
    parser.add_argument(
        '--create',
        action='store_true',
        help='创建数据库表'
    )
    
    parser.add_argument(
        '--drop',
        action='store_true',
        help='删除数据库表'
    )
    
    parser.add_argument(
        '--sample-data',
        action='store_true',
        help='插入示例数据'
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='重置数据库（删除并重新创建表）'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='显示数据库状态'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='测试数据库连接'
    )
    
    parser.add_argument(
        '--full-init',
        action='store_true',
        help='完整初始化（创建表 + 插入示例数据）'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制执行操作（跳过确认）'
    )
    
    args = parser.parse_args()
    
    # 检查是否至少指定了一个操作
    if not any([args.create, args.drop, args.sample_data, args.reset, 
                args.status, args.test, args.full_init]):
        parser.print_help()
        return
    
    try:
        initializer = DatabaseInitializer(args.config)
        
        # 测试连接
        if args.test:
            success = initializer.test_connection()
            sys.exit(0 if success else 1)
        
        # 显示状态
        if args.status:
            initializer.show_status()
            return
        
        # 危险操作确认
        if (args.drop or args.reset) and not args.force:
            response = input("此操作将删除所有数据，是否继续? (y/N): ").strip().lower()
            if response != 'y':
                logger.info("操作已取消")
                return
        
        # 执行操作
        if args.drop:
            initializer.drop_tables()
        
        if args.reset:
            initializer.reset_database()
        elif args.create or args.full_init:
            initializer.create_tables()
        
        if args.sample_data or args.full_init:
            initializer.insert_sample_data()
        
        logger.info("操作完成")
        
    except KeyboardInterrupt:
        logger.info("\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"操作失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()